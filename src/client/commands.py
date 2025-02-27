#! ------------ !#
#! EXPERIMENTAL !#
#! ------------ !#

COMMANDS = []


def Command():
    def wrapper(cls):
        COMMANDS.append(cls)
        return cls
    return wrapper

@Command
class DebugMode(Command):
    # Class Attributes
    description = "Enables or disables debug mode."
    is_admin = True,
    keyword = "debugmode"
    
    debugmode = False
    
    validate_args = [
        {"type": bool, "optional": True},
    ]
    
    def run(client, args):
        if args[0].lower() == "on":
            debugmode = True
        elif args[0].lower() == "off":
            debugmode = False
        elif args[0].lower() == "toggle":
            debugmode = not debugmode

        return f"Debug mode set to {debugmode}."
    
@Command
class Help(Command):
    description = "Displays a list of available commands."
    is_admin = False
    keyword = "help"
    
    validate_args = [
        {"command": str, "optional": True}
    ]
    
    # TODO: ADD DESCRIPTIONS FOR EACH COMMAND
    # /help debugmode
    # >> return DebugMode.description

    def populate(cls):
        help_descriptions = []
        
        for command in COMMANDS:
            help_descriptions.append(f"/{command.keyword}: {command.description}\n")
            
    def run(self): 
        return self.help_descriptionsasd


    
#     async def execute(self, client, args: list[str]):
#         await self.function(client, self.keyword, args)
        
#     async def c_help(client, keyword: str, args: list[str]):
        
#         print("Available commands:")
#         for command in COMMANDS:
#             print(f"{command.keyword}: {command.description}")

#     async def c_debugmode(client, keyword: str, args: list[str]):
#         pass


# async def c_debugmode(client, keyword: str, args: list[str]):
#     if len(args) < 1:
#         print("Usage: /debugmode [on|off|toggle]")
#         return
#     action = args[0].lower()
#     global DEBUG_ENABLED
#     if action == "on":
#         DEBUG_ENABLED = True
#     elif action == "off":
#         DEBUG_ENABLED = False
#     elif action == "toggle":
#         DEBUG_ENABLED = not DEBUG_ENABLED
#     else:
#         print("Usage: /debugmode [on|off|toggle]")
#         return
#     # Reconfigure loguru logger.
#     logger.remove()
#     new_level = "DEBUG" if DEBUG_ENABLED else "INFO"
#     logger.add(sys.stdout, level=new_level, colorize=True)
#     print(f"Debug mode set to {DEBUG_ENABLED}")

# async def c_msg(client, keyword: str, args: list[str]):
#     if len(args) < 2:
#         print("Usage: /msg <user> <message>")
#         return
#     pm_packet = packets.serverbound.direct_message(target=args[0], content=' '.join(args[1:]))
#     await client.send(pm_packet)

#     formatted_message = f"{Back.LIGHTBLUE_EX}{Fore.BLACK} DM {Style.RESET_ALL}{Style.DIM} You --> {Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}{args[0]}: {Style.RESET_ALL}{' '.join(args[1:])}"
#     print(formatted_message + Style.RESET_ALL)

# async def c_connect(client, keyword: str, args: list[str]):
#     if len(args) > 0:
#         await client.connect(args[0])
#     else:
#         await client.connect(client.nick)

# async def c_exit(client, keyword: str, args: list[str]):
#     if len(args) > 0:
#         await client.disconnect(' '.join(args[0:]))
#     else:
#         await client.disconnect()

Help.populate()

