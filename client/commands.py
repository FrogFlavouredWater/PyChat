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
            await websocket.send(f"__CMD__ {new_command}")
            return True
        else:
            print("Usage: /set debugmode [on|off|toggle]")
            return True
    return False

def command(func):
    def wrapper(*args, **kwargs):
        # Add functionality before the original function call
        result = func(*args, **kwargs)
        # Add functionality after the original function call
        await websocket.send(f"__MSG__ {result}")
    return wrapper

@command
def help():
    # Original function code
    pass

def init():
    # go through each command
    commands = []
    

