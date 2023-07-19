import math
from PyPav2 import Pavlok as pav


class TEMSError(Exception):
    pass


class TEMSDevice(object):
    def shock(self, intensity, duration):
        """intensity from 1 to 100, duration in seconds"""
        raise NotImplementedError

    def vibrate(self, intensity, duration):
        raise NotImplementedError


class Pavlok(TEMSDevice):
    config_options = {
        "mac_address": "MAC Address of Pavlok",
        "auto_discover": "Automatically discover Pavlok"
    }

    def __init__(self, config):
        self.config = config
        self.pav = pav()

        if "auto_discover" in self.config:
            mac_address = self.pav.discover()
            if not mac_address:
                raise TEMSError("Could not auto-discover your Pavlok. Try turning off Bluetooth on your phone, or pressing a button on the Pavlok to wake it up.")
            self.config["mac_address"] = mac_address
            del self.config["auto_discover"]

        if "mac_address" in self.config:
            self.pav.connect(self.config["mac_address"])
        else:
            raise TEMSError("Either auto-discover or MAC address must be entered")

    def shock(self, intensity, duration):
        # from https://github.com/ztrayl3/PyPav2, duration of Pavlok shock seems to be 0.7 seconds
        self.pav.shock(math.floor(intensity / 10), math.floor(duration / 0.7))

    def vibrate(self, intensity, duration):
        self.pav.vibrate(math.floor(intensity / 10), duration_on=duration)
