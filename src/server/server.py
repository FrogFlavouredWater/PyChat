import asyncio
import websockets
from loguru import logger
from SCPC.util import packets
# Dictionary mapping each connected websocket to its username.
clients = {}

packets.init("etc/cfg/packets.kdl")

async def broadcast(packet: packets.Packet):
    #logger.info("Broadcasting message: {}", message)
    if clients:
        await asyncio.gather(*[ws.send(packet.encode()) for ws in clients])

async def handle_server_command(websocket, username, message):
    """
    Handle commands that are meant to be processed by the server.
    Currently supports:
      /users list
    """
    return # TODO
    parts = message.strip().split()
    command = parts[0][1:].lower()  # Remove leading '/'
    if command == "users":
        if len(parts) == 2 and parts[1].lower() == "list":
            user_list = ", ".join(clients.values())
            await websocket.send(f"Connected users: {user_list}")
        else:
            await websocket.send("Usage: /users list")
        return True
    # Add more server commands here as needed.
    return False

async def chat_handler(websocket):
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    try:
        # The very first message from the client is taken as the username.
        join_pkt = await websocket.recv()
        username = packets.decode(join_pkt).nickname
        clients[websocket] = username
        logger.info("Client connected: {} ({})", username, client_ip)

        join_pkt = packets.clientbound.connect(nickname=username)
        await broadcast(join_pkt)

        async for message_packet in websocket:
            # If the message is a command event sent by the client (processed locally),
            # log it on the server and do not broadcast it.
            message = packets.decode(message_packet)
            # if message.type_name == "command":
            #     command_text = message.keyword
            #     logger.info("Command executed by {}: {}", username, command_text)
            #     continue
            # # If the message is a server-handled command, process it.
            # if message.startswith("/"):
            #     handled = await handle_server_command(websocket, username, message)
            #     if handled:
            #         logger.info("Command executed by {}: {}", username, message)
            #         continue uwu
            if message.type_name == "direct_message":
                pass # TODO

            elif message.type_name == "message":
                logger.debug("Received message from {}: {}", username, message.content)
                msg_pkt = packets.clientbound.recieve_message(nickname=username, content=message.content)
                await broadcast(msg_pkt)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed for client: {}", username)
    finally:
        if websocket in clients:
            username = clients.pop(websocket)

            leave_pkt = packets.clientbound.disconnect(nickname=username)
            await broadcast(leave_pkt)

async def main():
    logger.info("Starting server on 0.0.0.0:8080")
    async with websockets.serve(chat_handler, "0.0.0.0", 8080):
        logger.info("Server started. Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
