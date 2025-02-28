from loguru import logger
import sys

from common import cmd_utils
from common.cmd_utils import CommandResponse

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
            "name": "action",
            "type": "bool",
            "required": False
        }
    ]

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
