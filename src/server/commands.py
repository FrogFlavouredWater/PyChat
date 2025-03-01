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
