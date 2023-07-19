import math
from PyPav2 import Pavlok as pav
from playsound import playsound
import logging
import requests


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
    config_options = {
        "username": ("Username", str),
        "api_key": ("API Key", str),
        "code": ("Share Code", str),
    }

    def __init__(self, config):
        self.config = config
        self.session = requests.session()

    def api(self, intensity, duration, op):
        r = self.session.post("https://do.pishock.com/api/apioperate", json={
            "Username": self.config["username"],
            "Name": "ZeusIRL",
            "Code": self.config["code"],
            "Intensity": str(intensity),
            "Duration": str(duration),
            "Apikey": self.config["api_key"],
            "Op": op
        })
        logging.debug(f"pishock: {intensity},{duration},{op}: {r.status_code} {r.text}")

    def shock(self, intensity, duration):
        self.api(intensity, duration, "0")

    def vibrate(self, intensity, duration):
        self.api(intensity, duration, "1")


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
