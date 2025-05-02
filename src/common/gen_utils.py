import logging

class Response:
    """A class to manage general-purpose responses"""
    def __init__(self, success: bool, content: str = "", log: bool = False):
        self.success = success
        self.content = content

        if log:
            if success:
                logging.info(content)
            else:
                logging.warning(content)
        else:
            logging.debug(content)

    def __bool__(self):
        return self.success
