from loguru import logger
import sys
from colorama import Style, Fore, Back
from SCPC.util import packets

from common import cmd_utils

command_index = {}
command_aliases = {}

class Command(metaclass=cmd_utils.CommandRegistryMeta):
    @classmethod
    def register_command(cls, subclass):
        """Registers subclasses in the command_index"""
        command_index[subclass.keyword] = subclass # {"message": <message object>}
        for i in subclass.aliases:
            command_aliases[i] = subclass.keyword

class debugmode(Command):
    aliases = ["debug"]
    keyword = "debugmode"
    validation = [
        {
            "name": "action",
            "type": "bool",
            "required": False,
            "default": None
        }
    ]
    description = "Enable/disable debug mode"

    @classmethod
    async def invoke(cls, client, keyword: str, action: bool = None) -> tuple[int, str]:
        global DEBUG_ENABLED
        if action == None:
            DEBUG_ENABLED = not DEBUG_ENABLED
        else:
            DEBUG_ENABLED = action

        # Reconfigure loguru logger.
        logger.remove()
        new_level = "DEBUG" if DEBUG_ENABLED else "INFO"
        logger.add(sys.stdout, level=new_level, colorize=True)
        print(f"Debug mode set to {DEBUG_ENABLED}")
        return (0, "")

class message(Command):
    aliases = ["w", "dm", "pm", "msg"]
    keyword = "message"
    validation = [
        {
            "name": "target",
            "type": "string",
            "required": True
        },
        {
            "name": "content",
            "type": "string..",
            "required": True
        }
    ]
    description = "Send a message directly to someone"

    @classmethod
    async def invoke(cls, client, keyword: str, target: str, content: str):
        pm_packet = packets.serverbound.direct_message(target=target, content=content)
        await client.send(pm_packet)

        formatted_message = f"{Back.LIGHTBLUE_EX}{Fore.BLACK} DM {Style.RESET_ALL}{Style.DIM} You --> {Style.RESET_ALL}{Style.BRIGHT}{Fore.YELLOW}{target}: {Style.RESET_ALL}{content}"
        print(formatted_message + Style.RESET_ALL)

class connect(Command):
    aliases = []
    keyword = "connect"
    validation = [
        {
            "name": "nick",
            "type": "string",
            "required": False,
            "default": ""
        }
    ]
    description = "Reconnect to the server"

    @classmethod
    async def invoke(cls, client, keyword: str, nick: str):
        if nick:
            await client.connect(nick)
        else:
            await client.connect(client.nick)

class exit(Command):
    aliases = ["l", "disconnect"]
    keyword = "exit"
    validation = [
        {
            "name": "message",
            "type": "string",
            "required": False,
            "default": ""
        }
    ]
    description = "Leave the server with an optional message"

    @classmethod
    async def invoke(cls, client, keyword: str, message: str):
        await client.disconnect(message)

class help(Command):
    aliases = ["?"]
    keyword = "help"
    validation = [
        {
            "name": "command",
            "type": "string",
            "required": False,
            "default": ""
        }
    ]
    description = "List commands or give a description of a command"

    @classmethod
    async def invoke(cls, client, keyword: str, command: str):
        if command:
            if command in command_aliases:
                command = command_aliases[command]

            if command in command_index:
                cmd_class = command_index[command]
                print(cmd_utils.make_command_string(cmd_class.keyword, cmd_class.validation)) # Print human-readable command string
                try:
                    print(cmd_class.description)
                except AttributeError: # command has no description
                    pass

                print(f"Aliases: {', '.join(cmd_class.aliases)}")
            else:
                print(f"Command {command} not found")
        else:
            for key, cmd_class in command_index.items():
                print(cmd_utils.make_command_string(key, cmd_class.validation))

class emote(Command):
    keyword = "emote"
    aliases = ["e", "me"]
    validation = [
        {
            "name": "action",
            "type": "string..",
            "required": True
        }
    ]
    description = "Send a message as an action"

    @classmethod
    async def invoke(cls, client, keyword: str, action: str):
        msg_pkt = packets.serverbound.emote(content=action)
        await client.send(msg_pkt)
