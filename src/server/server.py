import asyncio
import websockets
from loguru import logger
from SCPC.util import packets
from common.conn import ConnectionHandler

MAX_MESSAGE_SIZE=100
SERVER_ADDRESS="0.0.0.0"
SERVER_PORT="8080"

command_aliases = {}

# Dictionary mapping each connected websocket to its username.
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

    async def p_connect(self, packet: packets.Packet):
        self.nick = packet.nickname
        clients.append(self)
        self.fully_connected = True
        return (0, "Connected")

    @if_fully_connected
    async def p_send_message(self, packet: packets.Packet):
        if len(packet.content) > MAX_MESSAGE_SIZE:
            logger.info(f"Message from {self.nick} blocked (too long)")
            return (1, "Message too long")
        logger.debug(f"Received message from {self.nick}: {packet.content}")
        msg_pkt = packets.clientbound.recieve_message(nickname=self.nick, content=packet.content)
        await broadcast(msg_pkt)
        return (0, "Sent")

    @if_fully_connected
    async def p_command(self, packet: packets.Packet):
        command_text = packet.keyword
        logger.info("Command executed by {}: {}", self.nick, command_text)
        return await self.handle_command(packet.keyword, packet.args)

    @if_fully_connected
    async def p_direct_message(self, packet: packets.Packet):
        if len(packet.content) > MAX_MESSAGE_SIZE:
            logger.info(f"Message from {self.nick} blocked (too long)")
            return (1, "Message too long")

        for key, value in clients.items():
            if value.lower() == packet.target.lower():
                dm_packet = packets.clientbound.direct_message(source=self.nick, content=packet.content)
                await key.send(dm_packet.encode())
                return (0, "Sent")
        return (2, "Target user not found")

    @if_fully_connected
    async def p_disconnect(self, packet: packets.Packet):
        dc_pkt = packets.clientbound.disconnect(nickname=self.nick, message=packet.message)
        await broadcast(dc_pkt)
        await self.conn.close()
        return (0, "")

    # TODO: REPEATED CODE: MOVE TO common.conn.ConnectionHandler
    async def handle_command(self, keyword: str, args: str) -> bool:
        cmd = args.split(' ')

        if command_aliases.get(keyword):
            keyword = command_aliases[keyword]

        try:
            cmd_func = getattr(self, "c_" + keyword) # Find the function in self that's named 'c_commandname'
        except AttributeError: # command not found
            return (3, "Command not found")

        await cmd_func(keyword, cmd)
        return (0, "Executed")

async def chat_handler(websocket: websockets.ClientConnection):
    client = Client(websocket)
    try:
        async for message_packet in websocket:
            try:
                message = packets.decode(message_packet)
            except packets.PacketReadError as e:
                logger.warning(f"Recieved invalid packet from {client.nick}: {e.args}")
            else:
                await client.handle_packet(message)

    except websockets.exceptions.ConnectionClosedError:
        logger.info("Connection closed for client: {}", client.nick)
        leave_pkt = packets.clientbound.disconnect(nickname=client.nick, message="Connection closed")
        await broadcast(leave_pkt)
    finally:
        if client in clients:
            clients.remove(client)

async def main():
    logger.info(f"Starting server on {SERVER_ADDRESS}:{SERVER_PORT}")
    async with websockets.serve(chat_handler, SERVER_ADDRESS, SERVER_PORT):
        logger.info("Server started. Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
