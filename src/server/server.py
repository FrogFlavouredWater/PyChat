import asyncio
import websockets
from loguru import logger
from SCPC.util import packets
from common.conn import ConnectionHandler

MAX_MESSAGE_SIZE=100
SERVER_ADDRESS="0.0.0.0"
SERVER_PORT="8080"

command_aliases = {"msg" : "message"}

clients = []

packets.init("etc/cfg/packets.kdl")

async def broadcast(packet: packets.Packet):
    #logger.info("Broadcasting message: {}", message)
    if clients:
        await asyncio.gather(*[client.send(packet) for client in clients])


class Client(ConnectionHandler):
    """Class to store Client attributes and methods"""
    def __init__(self, conn: websockets.ClientConnection, nick: str = ""):
        super().__init__(conn, nick)

    def if_fully_connected(func):
        async def wrapper(self, *args, **kwargs):
            # Is the client fully connected? (has sent the connect packet)
            if not self.fully_connected:
                error_packet = packets.twoway.response(value=127, content="Client connection not complete")
                await self.send(error_packet)
                return
            return await func(self, *args, **kwargs)
        return wrapper

    async def disconnect(self, message: str):
        dc_pkt = packets.clientbound.disconnect(nickname=self.nick, message=message)
        if self.fully_connected: await broadcast(dc_pkt)
        logger.info(f"User {self.nick} disconnected: {message}")
        await self.conn.close()
        self.is_connected = False
        return (0, "")

    async def p_connect(self, packet: packets.Packet):
        for client in clients:
            if client.nick.lower() == packet.nickname.lower():
                return (5, "Username already in use")
        self.nick = packet.nickname
        clients.append(self)
        self.fully_connected = True

        con_pkt = packets.clientbound.connect(nickname=self.nick)
        await broadcast(con_pkt)
        logger.info(f"User {self.nick} connected")
        return (0, "Connected")

    @if_fully_connected
    async def p_send_message(self, packet: packets.Packet):
        if len(packet.content) > MAX_MESSAGE_SIZE:
            logger.info(f"Message from {self.nick} blocked (too long)")
            return (1, "Message too long")

        if len(packet.content) == 0:
            logger.info(f"Message from {self.nick} blocked (empty)")
            return (4, "Empty message")

        logger.debug(f"Received message from {self.nick}: {packet.content}")
        msg_pkt = packets.clientbound.recieve_message(nickname=self.nick, content=packet.content)
        await broadcast(msg_pkt)
        return (0, "Sent")

    @if_fully_connected
    async def p_emote(self, packet: packets.Packet):
        #TODO: Convert to server command
        if len(packet.content) > MAX_MESSAGE_SIZE:
            logger.info(f"Message from {self.nick} blocked (too long)")
            return (1, "Message too long")

        if len(packet.content) == 0:
            logger.info(f"Message from {self.nick} blocked (empty)")
            return (4, "Empty message")

        logger.debug(f"Received emote from {self.nick}: {packet.content}")
        msg_pkt = packets.clientbound.emote(nickname=self.nick, content=packet.content)
        await broadcast(msg_pkt)
        return (0, "Sent")

    @if_fully_connected
    async def p_command(self, packet: packets.Packet):
        command_text = packet.keyword
        logger.info(f"Command executed by {self.nick}: {command_text}")
        return await self.handle_command(packet.keyword, packet.args)

    @if_fully_connected
    async def p_direct_message(self, packet: packets.Packet):
        if len(packet.content) > MAX_MESSAGE_SIZE:
            logger.info(f"Message from {self.nick} blocked (too long)")
            return (1, "Message too long")

        for client in clients:
            if client.nick.lower() == packet.target.lower():
                dm_packet = packets.clientbound.direct_message(source=self.nick, content=packet.content)
                await client.send(dm_packet)
                return (0, "Sent")
        return (2, "Target user not found")

    async def p_disconnect(self, packet: packets.Packet):
        await self.disconnect(packet.message)

    async def handle_command(self, keyword: str, args: str) -> bool:
        cmd = args.split(' ')

        if keyword in command_aliases.keys():
            keyword = command_aliases[keyword] # set to value section of alias

        try:
            cmd_func = getattr(self, "c_" + keyword) # Find the function in self that's named 'c_commandname'
        except AttributeError: # command not found
            return (3, "Command not found")

        await cmd_func(keyword, cmd)
        return (0, "Executed")

async def chat_handler(websocket: websockets.ClientConnection):
    client = Client(websocket)
    async for message_packet in websocket: # wait for packets and decode raw bytes back to text
        try:
            message = packets.decode(message_packet)
        except Exception as e:
            logger.warning(f"Error while reading packet from {client.nick}: {e.args}")
        else:
            await client.handle_packet(message)

    # once client disconnected
    if client in clients:
        clients.remove(client)

    if client.is_connected:
        await client.disconnect("Connection closed")

async def main():
    logger.info(f"Starting server on {SERVER_ADDRESS}:{SERVER_PORT}")
    async with websockets.serve(chat_handler, SERVER_ADDRESS, SERVER_PORT):
        logger.info("Server started. Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except OSError as e:
        logger.error(f"Service already running on that address: \nOnly one use of each socket address is normally permitted.\n(Address: {SERVER_ADDRESS}:{SERVER_PORT} is already in use)\nIs the server already running?\n")
    except Exception as e:
        logger.error(f"Server stopped due to error: {e}")



