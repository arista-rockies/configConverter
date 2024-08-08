from confparser import confparser
import yaml
import argparse
import pyavd.get_device_config
import re

parser = argparse.ArgumentParser()
parser.add_argument("-i", required=True, help="input file")
parser.add_argument("--dissector", default="ios.yaml", help="dissector file. default=ios.yaml")
parser.add_argument("--output", default="text", help="default=text, text|yaml")

args = parser.parse_args()

notifications = []

def setupInterface(interface, oldInterface):
    # this function will take the interface dict passed to it and convert it into
    #  pyavd config
    newInterface = {}
    if interface.startswith("Port") or interface.startswith("Vlan"):
        newInterface["name"] = interface
    else:
        intfName = interface.split('/')
        newInterface["name"] = f"ethernet{intfName[-1]}"

    if "description" in oldInterface:
        newInterface["description"] = oldInterface.pop("description")
    if "vlans" in oldInterface:
        newInterface["vlans"] = oldInterface.pop("vlans")
    if "mode" in oldInterface:
        newInterface["mode"] = oldInterface.pop("mode")
    if "shutdown" in oldInterface:
        newInterface["shutdown"] = oldInterface.pop("shutdown")
    if "mtu" in oldInterface:
        newInterface["mtu"] = oldInterface.pop("mtu")
    if "logging" in oldInterface:
        # i didn't see a way in the yaml to set a complex key structure so we need to do this by hand
        newInterface["logging"] = {}
        if "link-status" in oldInterface["logging"]:
            newInterface["logging"].update({"event": {"link_status": oldInterface["logging"].pop("link-status")}})

        if len(oldInterface["logging"]) == 0:
            oldInterface.pop("logging")

    if "link_trap" in oldInterface:
        newInterface["snmp_trap_link_change"] = oldInterface.pop("link_trap")

    if "storm_control" in oldInterface:
        newInterface["storm_control"] = {}
        if "broadcast" in oldInterface["storm_control"]:
            #FIXME - the pop returns a confparser class. this can't be the best way to cast this?
            newInterface["storm_control"]["broadcast"] = yaml.safe_load(f'{oldInterface["storm_control"].pop("broadcast")}')

        #FIXME storm_control action?
        """    "storm_control": {
                 "action": [
                     "shutdown",
                     "trap"
                 ]
               },"""
        #FIXME
        if "action" in oldInterface["storm_control"]:
            oldInterface["storm_control"].pop("action")

        if len(oldInterface["storm_control"]) == 0:
            oldInterface.pop("storm_control")

    if "lldp" in oldInterface:
        #FIXME - the pop returns a confparser class. this can't be the best way to cast this?
        newInterface["lldp"] = yaml.safe_load(f'{oldInterface.pop("lldp")}')

    # FIXME we need to do something special here
    #  our speed/duplex settings are pretty different than cisco
    #  presently we only look for 10m, 100m, 1000m
    #  the logic here is a bit messy. it's written long here for clarity
    #   ) if speed not set, leave default
    #   ) if duplex is not set, assume auto
    #   ) if duplex and speed set, forced

    if "10" in oldInterface.get("speed", []):
        notifications.append(f"!!!!!!!!!!!!!!! {interface} has 10Meg.  Care must be taken as to the destination switch capabilities!!!!")

    if not "speed" in oldInterface and "duplex" in oldInterface:
        oldInterface.pop("duplex")
    elif "speed" in oldInterface and not "duplex" in oldInterface:
        tmp = []
        for speed in oldInterface["speed"]:
            if speed == "auto":
                tmp.append("auto")
                continue
            if speed == "1":
                tmp.append("1gfull")
                tmp.append("1000full")
            elif speed == "100":
                tmp.append("100full")
                tmp.append("100half")
            elif speed == "10":
                tmp.append("10full")
                tmp.append("10half")
        newInterface["speed"] = " ".join(tmp)
        oldInterface.pop("speed")
    elif "speed" in oldInterface and "duplex" in oldInterface:
        # let's force this!
        newInterface["speed"] = f"{oldInterface['speed'][0]}{oldInterface['duplex']}"
        oldInterface.pop("speed")
        oldInterface.pop("duplex")
        
    if "spanning_tree_guard" in oldInterface:
        newInterface["spanning_tree_guard"] = oldInterface.pop("spanning_tree_guard")

    if "channel_group" in oldInterface:
        #FIXME - the pop returns a confparser class. this can't be the best way to cast this?
        newInterface["channel_group"] = yaml.safe_load(f'{oldInterface.pop("channel_group")}')

    if "native_vlan" in oldInterface:
        newInterface["native_vlan"] = oldInterface.pop("native_vlan")

    if "ipv4" in oldInterface and oldInterface["ipv4"] != False:
        #if "ethernet" in newInterface["name"].lower():
            #newInterface[] = no switchport
        newInterface["ip_address"] = oldInterface.pop("ipv4")

    if "ipv4_redirects" in oldInterface:
        newInterface["ip_icmp_redirect"] = oldInterface.pop("ipv4_redirects")

    if "ipv4_proxy_arp" in oldInterface:
        newInterface["ip_proxy_arp"] = oldInterface.pop("ipv4_proxy_arp")

    ##### these are things i don't care about
    if "cdp_enable" in oldInterface:
        oldInterface.pop("cdp_enable")
    if "dtp" in oldInterface:
        oldInterface.pop("dtp")
    if "encap" in oldInterface:
        oldInterface.pop("encap")
    if "switchport" in oldInterface:
        oldInterface.pop("switchport")


    # what's left?
    #print(yaml.dump(newInterface, sort_keys=False))
    if len(oldInterface) > 0:
        print(f"****** {newInterface['name']}")
        print(oldInterface)
        print("******")

    return newInterface

dissector = confparser.Dissector.from_file(args.dissector)
dev = dissector.parse_file(args.i)

newInterfaces = {
        "ethernet_interfaces": [],
        "vlan_interfaces": [],
        "port_channel_interfaces": []
}

for interface, interfaceConfig in dev["interface"].items():
    if interface.startswith("Gigabit"):
        newInterfaces["ethernet_interfaces"].append(setupInterface(interface, interfaceConfig))
    elif interface.startswith("Vlan"):
        newInterfaces["vlan_interfaces"].append(setupInterface(interface, interfaceConfig))
    elif interface.startswith("Port"):
        newInterfaces["port_channel_interfaces"].append(setupInterface(interface, interfaceConfig))

if args.output == "text":
    print(pyavd.get_device_config(newInterfaces))
elif args.output == "yaml":
    print(yaml.dump(newInterfaces))

for notification in notifications:
    print(notification)
