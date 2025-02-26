import asyncio
import websockets
from loguru import logger
from SCPC.util import packets
from SCPC.util import data_types as dt
# Dictionary mapping each connected websocket to its username.
clients = {}

async def broadcast(packet: packets.Packet):
    #logger.info("Broadcasting message: {}", message)
    if clients:
        await asyncio.gather(*[ws.send(packet) for ws in clients])

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
        username = await websocket.recv()
        clients[websocket] = username
        logger.info("Client connected: {} ({})", username, client_ip)

        join_pkt = packets.clientbound.connect()
        join_pkt.nickname = dt.lds(username)
        join_pkt.content = dt.nts()
        await broadcast(join_pkt)

        async for message in websocket:
            # If the message is a command event sent by the client (processed locally),
            # log it on the server and do not broadcast it.
            if message.startswith("__CMD__"):
                command_text = message[len("__CMD__"):].strip()
                logger.info("Command executed by {}: {}", username, command_text)
                continue
            # If the message is a server-handled command, process it.
            if message.startswith("/"):
                handled = await handle_server_command(websocket, username, message)
                if handled:
                    logger.info("Command executed by {}: {}", username, message)
                    continue
            logger.debug("Received message from {}: {}", username, message)
            msg_pkt = packets.clientbound.recieve_message()
            msg_pkt.nickname = dt.lds(username)
            msg_pkt.content = dt.nts(message.replace(dt.NULL_CHAR, ''))
            await broadcast(msg_pkt)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed for client: {}", username)
    finally:
        if websocket in clients:
            username = clients.pop(websocket)

            leave_pkt = packets.clientbound.disconnect()
            leave_pkt.nickname = dt.lds(username)
            leave_pkt.message = dt.nts()
            await broadcast(leave_pkt)

async def main():
    logger.info("Starting server on 0.0.0.0:8080")
    async with websockets.serve(chat_handler, "0.0.0.0", 8080):
        logger.info("Server started. Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
