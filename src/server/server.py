import asyncio
import websockets
from loguru import logger
from SCPC.util import packets
# Dictionary mapping each connected websocket to its username.
clients = []

packets.init("etc/cfg/packets.kdl")

async def broadcast(packet: packets.Packet):
    #logger.info("Broadcasting message: {}", message)
    if clients:
        await asyncio.gather(*[client.send(packet) for client in clients])

class Client:
    """Class to store Client attributes and methods"""
    def __init__(self, conn: websockets.ClientConnection, nick: str = ""):
        self.conn = conn
        self.addr = conn.remote_address[0] if conn.remote_address else ""
        self.nick = nick
        self.fully_connected = False

    def if_fully_connected(func):
        async def wrapper(self, *args, **kwargs):
            # Is the client fully connected? (has sent the connect packet)
            if not self.fully_connected:
                error_packet = packets.twoway.response(value=127, content="Client connection not complete")
                await self.send(error_packet)
                return (127, )
            return await func(self, *args, **kwargs)
        return wrapper

    async def handle_packet(self, packet: packets.Packet):
        packet_func = getattr(self, "p_" + packet.type_name)
        response = await packet_func(packet) # Call the function in self for the packet type
        if 'r' in packet.flags and response:
            resp_packet = packets.twoway.response(value=response[0], content=response[1])
            await self.send(resp_packet)

    async def send(self, packet: packets.Packet):
        await self.conn.send(packet.encode())

    async def p_connect(self, packet: packets.Packet):
        self.nick = packet.nickname
        clients.append(self)
        self.fully_connected = True
        return (0, "Connected")

    @if_fully_connected
    async def p_send_message(self, packet: packets.Packet):
        logger.debug("Received message from {}: {}", self.nick, packet.content)
        msg_pkt = packets.clientbound.recieve_message(nickname=self.nick, content=packet.content)
        await broadcast(msg_pkt)
        return (0, "Sent")

    @if_fully_connected
    async def p_command(self, packet: packets.Packet):
        command_text = packet.keyword
        logger.info("Command executed by {}: {}", self.nick, command_text)
        return (0, "Executed")

    @if_fully_connected
    async def p_direct_message(self, packet: packets.Packet):
        for key, value in clients.items():
            if value.lower() == packet.target.lower():
                dm_packet = packets.clientbound.direct_message(source=self.nick, content=packet.content)
                await key.send(dm_packet.encode())
                return (0, "Sent")
        return (1, "Target user not found")

    @if_fully_connected
    async def p_disconnect(self, packet: packets.Packet):
        dc_pkt = packets.clientbound.disconnect(nickname=self.nick, message=packet.message)
        await broadcast(dc_pkt)
        await packet.close()
        return (0, )

async def chat_handler(websocket: websockets.ClientConnection):
    client = Client(websocket)
    try:
        async for message_packet in websocket:
            message = packets.decode(message_packet)
            await client.handle_packet(message)

    except websockets.exceptions.ConnectionClosedError:
        logger.info("Connection closed for client: {}", client.nick)
        leave_pkt = packets.clientbound.disconnect(nickname=client.nick, message="Connection closed")
        await broadcast(leave_pkt)
    finally:
        if client in clients:
            clients.pop(client)

async def main():
    logger.info("Starting server on 0.0.0.0:8080")
    async with websockets.serve(chat_handler, "0.0.0.0", 8080):
        logger.info("Server started. Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
