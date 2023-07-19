import math
from PyPav2 import Pavlok as pav
from playsound import playsound
import logging


class TEMSError(Exception):
    pass


class TEMSDevice(object):
    def shock(self, intensity, duration):
        """intensity from 1 to 100, duration in seconds"""
        raise NotImplementedError

    def vibrate(self, intensity, duration):
        """intensity from 1 to 100, duration in seconds"""
        raise NotImplementedError


class PiShock(TEMSDevice):
    pass

class Pavlok(TEMSDevice):
    config_options = {
        "mac_address": ("MAC Address of Pavlok", str)
    }

    def __init__(self, config):
        self.config = config
        self.pav = pav()

        if "mac_address" in self.config:
            self.pav.connect(self.config["mac_address"])
        else:
            logging.error("MAC address must be entered.")
            raise TEMSError("MAC address must be entered")

    def shock(self, intensity, duration):
        # from https://github.com/ztrayl3/PyPav2, duration of Pavlok shock seems to be 0.7 seconds
        self.pav.shock(math.floor(intensity / 10), math.floor(duration / 0.7))

    def vibrate(self, intensity, duration):
        self.pav.vibrate(math.floor(intensity / 10), duration_on=duration)


class Dummy(TEMSDevice):
    def __init__(self, config):
        self.config = {}

    def shock(self, intensity, duration):
        playsound("zeus.mp3")

    def vibrate(self, intensity, duration):
        playsound("vibe.mp3")


device_map = {
    "PiShock": PiShock,
    "Pavlok 3": Pavlok,
    "Dummy Device": Dummy
}
