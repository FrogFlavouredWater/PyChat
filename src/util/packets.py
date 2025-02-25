# ------------ #
# EXPERIMENTAL #
# ------------ #

import kdl

class Packet:
    """The base class which will be populated on load"""
    pass

class Packets:
    """The class which contains all packet types"""
    pass

# Load config file
with open("res/util/packets.kdl", 'r') as _infile:
    pkt_cfg = kdl.parse(_infile.read())

for i in pkt_cfg.nodes:
    # Create a dictionary of attributes for our new class
    attr_dict = {"id": i.args[0]}


    # Create a new class for the configured packet
    new_packet = type(i.name, (Packet, ), )

    # Assign the new packet class as an attribute of Packets
    setattr(Packets, i.name, new_packet)

if __name__ == "__main__":
    print(hex(Packets.send_message.id))
