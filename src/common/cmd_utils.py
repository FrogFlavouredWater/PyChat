class CommandRegistryMeta(type):
    """Metaclass which will run register() on all classes which inherit from this one"""
    def __init__(cls, name, bases, class_dict):
        super().__init__(name, bases, class_dict)
        if bases: # Is this class (e.g. msg) inheriting from the class using this meta (Command)?
            cls.register_class(cls) # Run register_class() on the parent class

