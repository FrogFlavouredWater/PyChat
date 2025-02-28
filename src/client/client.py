import asyncio
import websockets
from loguru import logger
import sys
import argparse
import kdl
from colorama import Style, Fore, Back
import aioconsole
from SCPC.util import packets

#import commands
from common.conn import ConnectionHandler
import commands
from common import cmd_utils

packets.init("etc/cfg/packets.kdl")

# Load config file
with open("etc/cfg/config.kdl", 'r') as _infile:
    client_cfg = kdl.parse(_infile.read())

IP_ADDR = client_cfg["client"]["server"]["ip"].args[0]
IP_PORT = client_cfg["client"]["server"]["port"].args[0]

DEBUG_ENABLED = False
# TODO: add to config file

class Client(ConnectionHandler):
    """Class to store Client attributes and methods"""
    def __init__(self, conn: websockets.ClientConnection, nick: str = ""):
        super().__init__(conn, nick)

    async def connect(self, username: str):
        connect_pkt = packets.serverbound.connect(nickname=username)
        await self.send(connect_pkt)
        logger.info("Connected to server as {}", username)
        self.username = username

    async def disconnect(self, message: str = ""):
        print(1)
        await self.send(packets.serverbound.disconnect(message=message))
        self.is_connected = False

    async def p_keep_alive(self, packet: packets.Packet):
        return (0, "")

    async def p_recieve_message(self, packet: packets.Packet):
        print(f"{Fore.CYAN}{packet.nickname}: {Style.RESET_ALL}{packet.content}{Style.RESET_ALL}")

    async def p_connect(self, packet: packets.Packet):
        print(f"{Fore.MAGENTA}{packet.nickname} joined the server{(': ' + packet.message) if packet.message else ''}{Style.RESET_ALL}") # message is an optional field containing a join/leave reason

    async def p_disconnect(self, packet: packets.Packet):
        print(f"{Fore.MAGENTA}{packet.nickname} left the server{(': ' + packet.message) if packet.message else ''}{Style.RESET_ALL}")

    async def p_direct_message(self, packet: packets.Packet):
        print(f"{Back.LIGHTBLUE_EX}{Fore.BLACK} DM {Style.RESET_ALL} {Style.BRIGHT}{Fore.YELLOW}{packet.source}{Style.RESET_ALL}{Style.DIM} --> You: {Style.RESET_ALL}{packet.content}{Style.RESET_ALL}")

    async def p_response(self, packet: packets.Packet):
        if packet.value > 0:
            logger.error(f"Server returned faliure {packet.value}: {packet.content}")
        else:
            logger.debug(f"Server returned a success: {packet.content}")

    async def handle_command(self, command: str) -> bool:
        cmd = command.lstrip('/').split(' ')
        if len(cmd) == 0:
            return False

        keyword = cmd.pop(0) # get 1st phrase of command
        if commands.command_aliases.get(keyword):
            keyword = commands.command_aliases[keyword]

        if keyword in commands.command_index:
            cmd_class = commands.command_index[keyword]
        else: # defer to server
            cmd_pkt = packets.serverbound.command(keyword=keyword, args=' '.join(cmd))
            await self.send(cmd_pkt)
            logger.debug("Sent command: {}", keyword)
            return False

        try:
            args = cmd_utils.validate_args(cmd, cmd_class.validation)
        except:
            print("Usage: ", cmd_utils.make_command_string(cmd_class.keyword, cmd_class.validation))
            return False

        await cmd_class.invoke(self, keyword, **args)
        return True

async def send_messages(client: Client):
    # Continuously read user input and send messages.
    while client.is_connected:
        # Green prompt for user input.
        msg = await aioconsole.ainput(f"{Fore.GREEN}>> {Style.RESET_ALL}")

        # Process local commands (e.g. /set debugmode or /dm)
        if msg.startswith("/"):
            await client.handle_command(msg)
            continue

        if len(msg) > 0:
            msg_pkt = packets.serverbound.send_message(content=msg)
            await client.send(msg_pkt)
            logger.debug("Sent message: {}", msg)

async def receive_messages(client: Client):
    async for encoded_packet in client.conn:
        try:
            packet = packets.decode(encoded_packet)
        except packets.PacketReadError as e:
            logger.warning(f"Recieved invalid packet from server: {e.args}")
        else:
            await client.handle_packet(packet)

        if not client.is_connected: break


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
        await client.connect(username)
        # Run both send and receive loops concurrently.
        await asyncio.gather(send_messages(client), receive_messages(client))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    try:
        asyncio.run(main())
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed by server.")
    except KeyboardInterrupt:
        pass
    except ConnectionRefusedError:
        logger.critical("Connection refused by server.\nIs the server running?\nIs the IP address correct?\nIs the port correct?\nAre you connected to the internet?\nAre you really connected to the internet?\nAre you sure?\nAre you really sure?\nAre you really really sure?\nAre you really really really sure?")
    except Exception as e: #^ IMPORTANT: HENRY DONT YOU FUCKING DARE REMOVE THIS
        logger.critical(f"Something went wrong and I have no fucking clue what it was. Good luck debugging this one:\n Maybe it was: {e}")