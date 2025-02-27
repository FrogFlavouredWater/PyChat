import asyncio
import websockets
from loguru import logger
import sys
import argparse
from SCPC.util import packets
import kdl
from colorama import Style, Fore, Back
from common.conn import ConnectionHandler

packets.init("etc/cfg/packets.kdl")

# Load config file
with open("etc/cfg/config.kdl", 'r') as _infile:
    client_cfg = kdl.parse(_infile.read())

IP_ADDR = client_cfg.get("client").get("server").props["ip"]
IP_PORT = client_cfg.get("client").get("server").props["port"]

DEBUG_ENABLED = False

class Client(ConnectionHandler):
    """Class to store Client attributes and methods"""
    def __init__(self, conn: websockets.ClientConnection, nick: str = ""):
        super().__init__(conn, nick)

    async def p_recieve_message(self, packet: packets.Packet):
        print(f"{Fore.CYAN}{packet.nickname}: {Style.RESET_ALL}{packet.content}")

    async def p_connect(self, packet: packets.Packet):
        print(f"{Fore.MAGENTA}{packet.nickname} joined the server{(': ' + packet.message) if packet.message else ''}") # message is an optional field containing a join/leave reason

    async def p_disconnect(self, packet: packets.Packet):
        print(f"{Fore.MAGENTA}{packet.nickname} left the server{(': ' + packet.message) if packet.message else ''}")

    async def p_direct_message(self, packet: packets.Packet):
        print(f"{Back.LIGHTBLUE_EX}{Fore.BLACK} DM {Style.RESET_ALL} {Style.BRIGHT}{Fore.YELLOW}{packet.source}{Style.RESET_ALL}{Style.DIM} --> You: {Style.RESET_ALL}{packet.content}")

    async def p_response(self, packet: packets.Packet):
        if packet.value > 0:
            logger.error(f"Server returned faliure {packet.value}: {packet.content}")
        else:
            logger.debug(f"Server returned a success: {packet.content}")

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

async def send_messages(client: Client):
    # Continuously read user input and send messages.
    while True:
        # Green prompt for user input.
        msg = await asyncio.to_thread(input, "\033[32m>> \033[0m")
        if msg.lower() == "exit":
            await client.send(packets.serverbound.disconnect())
            break
        # Process local commands (e.g. /set debugmode or /dm).
        if msg.startswith("/"):
            handled = await handle_client_command(client.conn, msg)
            if handled:
                continue  # Skip sending the command if it was handled locally.

        msg_pkt = packets.serverbound.send_message(content=msg)
        await client.send(msg_pkt)
        logger.debug("Sent message: {}", msg)

async def receive_messages(client: Client):
    try:
        async for encoded_packet in client.conn:
            packet = packets.decode(encoded_packet)
            await client.handle_packet(packet)

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
        client = Client(websocket, username)
        # Send the username as the first message.
        connect_pkt = packets.serverbound.connect(nickname=username)
        await client.send(connect_pkt)
        logger.info("Connected to server as {}", username)
        # Run both send and receive loops concurrently.
        await asyncio.gather(send_messages(client), receive_messages(client))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    asyncio.run(main())
