import asyncio
import websockets
from loguru import logger
import sys
import argparse
from SCPC.util import packets
from SCPC.util import datatypes as dt
import kdl

# Load config file
with open("res/cfg/config.kdl", 'r') as _infile:
    client_cfg = kdl.parse(_infile.read())

IP_ADDR = client_cfg.client.server.ip
PORT = client_cfg.client.server.port

DEBUG_ENABLED = False

async def handle_client_command(websocket, message):
    """
    Process client-specific commands.
    Supports:
      /set debugmode on|off|toggle
      /dm on|off|toggle (alias for /set debugmode)
    If handled locally, the function sends a command event to the server
    so that the server logs the command execution.
    Returns True if the command was handled locally.
    """
    parts = message.strip().split()
    if not parts:
        return False

    # Check for aliases: /dm becomes /set debugmode
    if parts[0].lower() in ["/dm", "/set"]:
        if parts[0].lower() == "/dm":
            parts = ["/set", "debugmode"] + parts[1:]
        new_command = " ".join(parts)
        if parts[1].lower() == "debugmode":
            if len(parts) < 3:
                print("Usage: /set debugmode [on|off|toggle]")
                return True
            action = parts[2].lower()
            global DEBUG_ENABLED
            if action == "on":
                DEBUG_ENABLED = True
            elif action == "off":
                DEBUG_ENABLED = False
            elif action == "toggle":
                DEBUG_ENABLED = not DEBUG_ENABLED
            else:
                print("Usage: /set debugmode [on|off|toggle]")
                return True
            # Reconfigure loguru logger.
            logger.remove()
            new_level = "DEBUG" if DEBUG_ENABLED else "INFO"
            logger.add(sys.stdout, level=new_level, colorize=True)
            print(f"Debug mode set to {DEBUG_ENABLED}")
            # Send a special command event to the server for logging.
            #await websocket.send(f"__CMD__ {new_command}")
            return True
        else:
            print("Usage: /set debugmode [on|off|toggle]")
            return True
    return False

async def send_messages(websocket):
    # Continuously read user input and send messages.
    while True:
        # Green prompt for user input.
        msg = await asyncio.to_thread(input, "\033[32m>> \033[0m")
        if msg.lower() == "exit":
            await websocket.close()
            break
        # Process local commands (e.g. /set debugmode or /dm).
        if msg.startswith("/"):
            handled = await handle_client_command(websocket, msg)
            if handled:
                continue  # Skip sending the command if it was handled locally.

        msg_pkt = packets.serverbound.send_message()
        msg_pkt.content = dt.nts(msg)
        await websocket.send(msg_pkt)
        logger.debug("Sent message: {}", msg)

async def receive_messages(websocket):
    try:
        async for message in websocket:
            print("MESSAGE: ", message)
            # Format incoming messages:
            # System messages (in brackets) appear in magenta,
            # user list messages in yellow, and chat messages in cyan. :3
            if message.startswith("[") and message.endswith("]"):
                formatted_message = f"\033[35m{message}\033[0m"
            elif message.startswith("Connected users:"):
                formatted_message = f"\033[33m{message}\033[0m"
            else:
                formatted_message = f"\033[36m{message}\033[0m"
            # Prepend a newline so it doesn't interfere with the prompt.
            print("\n" + formatted_message)
            logger.debug("Received message: {}", message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed by server.")


async def main(debug):
    # Configure loguru logging.
    logger.remove()
    global DEBUG_ENABLED
    DEBUG_ENABLED = debug
    if debug:
        logger.add(sys.stdout, level="DEBUG", colorize=True)
        logger.debug("Debug mode enabled.")
    else:
        logger.add(sys.stdout, level="INFO", colorize=True)

    username = await asyncio.to_thread(input, "Enter your username: ")
    url = f"ws://{IP_ADDR}:{PORT}"
    async with websockets.connect(url) as websocket:
        # Send the username as the first message.
        connect_pkt = packets.serverbound.connect()
        connect_pkt.username = dt.lds(username)
        await websocket.send(connect_pkt)
        logger.info("Connected to server as {}", username)
        # Run both send and receive loops concurrently.
        await asyncio.gather(send_messages(websocket), receive_messages(websocket))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    asyncio.run(main(args.debug))
