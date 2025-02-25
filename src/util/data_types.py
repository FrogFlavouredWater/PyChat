import unicodedata

class uint:
    NUM_BYTES = 0
    def __init__(self, value: int=0):
        self.MAX_VALUE = 2**(self.NUM_BYTES * 8)

        if value > self.MAX_VALUE: raise OverflowError(f"Value {value} too large for 8-bit uint")
        if value < 0: raise TypeError(f"{value} is not an unsigned integer")

        self.value = value

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def encode(self):
        """Turn stored value into bytes"""
        return self.value.to_bytes(self.NUM_BYTES)

    @classmethod
    def decode(cls, value: bytes):
        """Turn bytes into this class"""
        if len(value) != cls.NUM_BYTES:
            raise TypeError("Wrong number of bytes")

        return cls(int.from_bytes(value))

class uint8(uint):
    NUM_BYTES = 1

class uint16(uint):
    NUM_BYTES = 1

class uint24(uint):
    NUM_BYTES = 1

class uint32(uint):
    NUM_BYTES = 1

class lds:
    def __init__(self, value: str=""):
        if len(value) > 255:
            raise OverflowError("String too long for LDS, use NTS instead")

        self.value = value

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return self.value

    def encode(self):
        """Turn stored value into bytes"""
        enc = bytearray(len(self.value))
        enc.append(self.value.encode('unicode_escape'))

        return bytes(enc)

    @classmethod
    def decode(cls, value: bytes):
        """Turn bytes into this class"""
        length = int.from_bytes(value[0])

        if len(value)-1 != length:
            raise TypeError("Wrong number of bytes")

        return cls(int.from_bytes(value))
