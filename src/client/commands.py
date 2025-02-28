from loguru import logger
import sys

from common import cmd_utils

command_index = {}

class Command(metaclass=cmd_utils.CommandRegistryMeta):
    @classmethod
    def register_command(cls, subclass):
        """Registers subclasses in the command_index"""
        command_index[subclass.__name__] = subclass # {"message": <message object>}

class debugmode(Command):
    aliases = ["debug"]
    args = [
        {
            "type": "bool",
            "required": False
        }
    ]

    async def invoke(cls, client, keyword: str, args: list[str]):
        if len(args) < 1:
            print("Usage: /debugmode [on|off|toggle]")
            return
        action = args[0].lower()
        global DEBUG_ENABLED
        if action == "on":
            DEBUG_ENABLED = True
        elif action == "off":
            DEBUG_ENABLED = False
        elif action == "toggle":
            DEBUG_ENABLED = not DEBUG_ENABLED
        else:
            print("Usage: /debugmode [on|off|toggle]")
            return
        # Reconfigure loguru logger.
        logger.remove()
        new_level = "DEBUG" if DEBUG_ENABLED else "INFO"
        logger.add(sys.stdout, level=new_level, colorize=True)
        print(f"Debug mode set to {DEBUG_ENABLED}")
