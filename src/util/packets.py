# ------------ #
# EXPERIMENTAL #
# ------------ #

import kdl
import data_types as dt

class Packet:
    """The base class which will be populated on load"""
    pass

version_major = 0
version_minor = 0

"""The classes which contains all packet types"""
class serverbound: pass
class clientbound: pass

# Load config file
with open("res/util/packets.kdl", 'r') as _infile:
    pkt_cfg = kdl.parse(_infile.read())

for i in pkt_cfg.nodes:
    if i.name == "version":
        version_major = i.args[0]
        version_minor = i.args[1]
        continue

    for n in i.nodes:
        # Create a dictionary of attributes for our new class
        attr_dict = {"id": n.args[0], "flags":list(n.args[1]), "fields": n.props}

        # Create a new class for the configured packet
        new_packet = type(n.name, (Packet, ), )

        # new_packet is now a class with the name of what was given in packets.kdl and contains:
        # id: the ID as an int
        # flags: a list of single characters indicating the packet flags
        # fields: a dictionary of attribute names and the name of their types as defined in data_types.py

        # Assign the new packet class as an attribute
        if i.name in ["serverbound", "twoway"]:
            setattr(serverbound, n.name, new_packet)
        elif i.name in ["clientbound", "twoway"]:
            setattr(clientbound, n.name, new_packet)

        # From another script, we can access e.g. packets.serverbound.connect.id and get 0x4002

if __name__ == "__main__":
    pass
