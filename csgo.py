import winreg
from pathlib import Path
from flask import Flask, request
import threading

config = """"Console Sample v.1"
{
 "uri" "http://127.0.0.1:55608"
 "buffer"  "0.0"
 "data"
 {
   "provider"            "1"
   "player_id"           "1"
   "player_state"        "1"      // player state for this current round such as health, armor, kills this round, etc.
 }
}
"""


def steam_folder():
    return winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Valve\\Steam"), "SteamPath")[0]


def gse_fname():
    return Path(steam_folder()) / "steamapps/common/Counter-Strike Global Offensive/csgo/cfg/gamestate_integration_pavshock.cfg"


def check_gse():
    if gse_fname().exists():
        with open(gse_fname()) as f:
            if f.read() == config:
                return True

    return False


def configure_gse():
    with open(gse_fname(), "w") as f:
        f.write(config)


class CSGOGSEHandler(object):
    def __init__(self):
        self.app = Flask("gse")
        self.app.add_url_rule("/", "gse", self.gse_handler, methods=["POST"])

    def start(self):
        t = threading.Thread(target=lambda: self.app.run(host="127.0.0.1", port=55608, debug=False))
        t.setDaemon(True)
        t.start()

    @staticmethod
    def on_death():
        raise NotImplementedError

    @staticmethod
    def on_hit(self):
        raise NotImplementedError

    def gse_handler(self):
        current_health = request.json.get("player", {}).get("state", {}).get("health", 100)
        previous_health = request.json.get("previously", {}).get("player", {}).get("state", {}).get("health", 0)

        if current_health == 0:
            if previous_health > current_health:
                if request.json["provider"]["steamid"] == request.json["player"]["steamid"]:
                    self.on_death()

        return '', 204


if __name__ == "__main__":
    # for testing
    CSGOGSEHandler().app.run(host="127.0.0.1", port=55608, debug=True)
