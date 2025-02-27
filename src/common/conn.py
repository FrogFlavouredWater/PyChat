import websockets
from SCPC.util import packets

class ConnectionHandler:
    def __init__(self, conn: websockets.ClientConnection, nick: str = ""):
        self.conn = conn
        self.addr = conn.remote_address[0] if conn.remote_address else ""
        self.nick = nick
        self.fully_connected = False

    async def handle_packet(self, packet: packets.Packet):
        packet_func = getattr(self, "p_" + packet.type_name) # Find the function in self that's named 'p_packettype'
        response = await packet_func(packet) # Call the function
        if 'r' in packet.flags and response: # Does this packet type say a response is wanted?
            resp_packet = packets.twoway.response(value=response[0], content=response[1])
            await self.send(resp_packet) # send response

    async def send(self, packet: packets.Packet):
        await self.conn.send(packet.encode())
