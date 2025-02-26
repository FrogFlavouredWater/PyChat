import asyncio
import websockets
from loguru import logger
import sys
import argparse
from SCPC.util import packets
import kdl
from colorama import Style, Fore, Back

packets.init("etc/cfg/packets.kdl")

# Load config file
with open("etc/cfg/config.kdl", 'r') as _infile:
    client_cfg = kdl.parse(_infile.read())

IP_ADDR = client_cfg.get("client").get("server").props["ip"]
IP_PORT = client_cfg.get("client").get("server").props["port"]

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
            pkt = packets.serverbound.command(keyword=parts[0])
            await websocket.send(pkt.encode())
            return True
        else:
            print("Usage: /set debugmode [on|off|toggle]")
            return True
    elif parts[0].lower() == "/pm":
        if len(parts) < 3:
            print("Usage: /pm <user> <message>")
            return True
        pm_packet = packets.serverbound.direct_message(target=parts[1], content=parts[2])
        await websocket.send(pm_packet.encode())

        formatted_message = f"{Back.LIGHTBLUE_EX}{Fore.BLACK}DM{Style.RESET_ALL}{Style.DIM} You --> {Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}{parts[1]}: {Style.RESET_ALL}{parts[2]}"
        print(formatted_message + Style.RESET_ALL)
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

        msg_pkt = packets.serverbound.send_message(content=msg)
        await websocket.send(msg_pkt.encode())
        logger.debug("Sent message: {}", msg)

async def receive_messages(websocket):
    try:
        async for message_packet in websocket:
            message = packets.decode(message_packet)
            # Format incoming messages:
            # System messages (in brackets) appear in magenta,
            # user list messages in yellow, and chat messages in cyan. :3
            if message.type_name == "recieve_message":
                formatted_message = f"{Fore.CYAN}{message.nickname}: {Style.RESET_ALL}{message.content}"
            elif message.type_name == "connect" or message.type_name == "disconnect":
                formatted_message = f"{Fore.MAGENTA}{message.nickname} joined the server{(': ' + message.message) if message.message else ''}" # message is an optional field containing a join/leave reason
            elif message.type_name == "direct_message":
                formatted_message = f"{Back.LIGHTBLUE_EX}{Fore.BLACK}DM{Style.RESET_ALL} {Style.BRIGHT}{Fore.YELLOW}{message.source}{Style.RESET_ALL}{Style.DIM} --> You: {Style.RESET_ALL}{message.content}"
            else:
                formatted_message = f"{Fore.YELLOW}{message.content}"
            # Prepend a newline so it doesn't interfere with the prompt.
            print(formatted_message + Style.RESET_ALL)
            logger.debug("Received message: {}", message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed by server.")


async def main():
    # Configure loguru logging.
    logger.remove()
    if DEBUG_ENABLED:
        logger.add(sys.stdout, level="DEBUG", colorize=True)
        logger.debug("Debug mode enabled.")
    else:
        logger.add(sys.stdout, level="INFO", colorize=True)

    username = await asyncio.to_thread(input, "Enter your username: ")
    url = f"ws://{IP_ADDR}:{IP_PORT}"
    async with websockets.connect(url) as websocket:
        # Send the username as the first message.
        connect_pkt = packets.serverbound.connect(nickname=username)
        await websocket.send(connect_pkt.encode())
        logger.info("Connected to server as {}", username)
        # Run both send and receive loops concurrently.
        await asyncio.gather(send_messages(websocket), receive_messages(websocket))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    asyncio.run(main())
