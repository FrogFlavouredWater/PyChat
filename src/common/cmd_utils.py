class CommandRegistryMeta(type):
    """Metaclass which will run register() on all classes which inherit from this one"""
    def __init__(cls, name, bases, class_dict):
        super().__init__(name, bases, class_dict)
        if bases: # Is this class (e.g. msg) inheriting from the class using this meta (Command)?
            cls.register_command(cls) # Run register_command() on the parent class

class CommandValidationKeyError(Exception):
    pass

def validate_args(args: list, validation: list) -> dict:
    """Takes a list of arguments and validation keys and returns the formatted args
    Raise an exception if args does not comply with validation input"""
    result = {}
    required = True
    repeat = False

    for i, key in enumerate(validation):
        # Has there already been a repeating argument?
        if repeat:
            raise CommandValidationKeyError("No arguments allowed after repeating arg")

        # Is the current value required while the last wasn't?
        # If so, the validation key is flawed, because a required argument cannot be after an optional arg
        if key['required'] and not required:
            raise CommandValidationKeyError("Required argument cannot be after optional argument")

        try:
            arg = args[i]
        except IndexError:
            #^ refactor
            if key['required']:
                raise IndexError
            else:
                arg = key['default']
                result[key['name']] = arg
                continue

        match key['type']:
            case "string..": # String that uses the remainder of the command (e.g. "/msg user hello how are you?") <- all arguments after 'user' are considered part of the same argument
                arg = ' '.join(args[i:])
                repeat = True
            case "string": pass # already string
            case "int": arg = int(arg)
            case "bool":
                arg = arg.lower()
                if arg in ["on", "yes", "true", "y"]:
                    arg = True
                elif arg in ["off", "no", "false", "n"]:
                    arg = False
                else:
                    raise AssertionError
            case "float": arg = float(arg)
            case "option":
                arg = arg.lower()
                assert arg in key["options"]

        if "max_value" in key:
            assert arg <= key['max_value']

        if "min_value" in key:
            assert arg >= key['min_value']

        result[key['name']] = arg

    return result

def make_command_string(keyword: str, validation: list) -> str:
    """Turn command information into a human-readable string"""
    command_str = f"/{keyword}"
    for i in validation:
        arg_str = ""

        if i['type'] == "option":
            arg_str = '|'.join(i['options']) # option1|option2
        else:
            arg_str = f"<{i['name']}>" # <name>

        if not i['required']:
            arg_str = f"[{arg_str}]" # [<name>]

        if i['type'] == "string..":
            arg_str += f"..." # <name>...

        command_str += f" {arg_str}"

    return command_str
