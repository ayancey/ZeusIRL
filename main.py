import wx
from pavshock import PavShock
import csgo
from tems import Pavlok, PiShock, TEMSDevice, TEMSError, device_map
from pathlib import Path
import json
import random
import logging
import sys

file_handler = logging.FileHandler(filename='log.log', encoding="utf-8")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

# ZeusMate
# Zeus2
# ZeusIRL


def save_device_config(name, config):
    if not Path("config").is_dir():
        Path("config").mkdir()

    with open(Path("config") / f"{name}.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
        logging.debug(f"saved {name} config: {config}")


def load_device_config(name):
    if not Path("config").is_dir():
        Path("config").mkdir()

    fi = Path("config") / f"{name}.json"
    if fi.exists():
        with open(fi) as f:
            config = f.read()
            logging.debug(f"loaded {name} config: {config}")
            return json.loads(config)
    return {}


class PavShockHandler(PavShock):
    def __init__(self, parent):
        super().__init__(parent)

        # Load devices from tems device map
        self.device_change_dropdown.Set(list(device_map.keys()))
        self.device_change_dropdown.SetSelection(0)

        self.device_config = load_device_config(self.device_change_dropdown.StringSelection)
        self.device = None

        # GSI Setup
        self.gse = csgo.CSGOGSEHandler()
        self.gse.on_death = self.on_death
        self.gse.on_hit = self.on_hit
        self.gse.start()

        self.armed = False

        self.shock_options = [
            self.max_intensity_slider,
            self.test_mode_checkbox,
            self.shock_on_death_checkbox,
            self.shock_on_hit_checkbox,
            self.randomize_intensity_checkbox,
            self.russian_enable_checkbox,
            self.russian_chance_slider,
            self.connect_button
        ]

        self.options_to_save = [
            (self.device_change_dropdown, "device"),
            (self.max_intensity_slider, "intensity"),
            (self.test_mode_checkbox, "test_mode"),
            (self.shock_on_death_checkbox, "shock_on_death"),
            (self.shock_on_hit_checkbox, "shock_on_hit"),
            (self.randomize_intensity_checkbox, "randomize_intensity"),
            (self.russian_enable_checkbox, "russian_roulette"),
            (self.russian_chance_slider, "russian_chance")
        ]

        self.load_options()

    def save_options(self):
        if not Path("config").is_dir():
            Path("config").mkdir()

        options = {}

        for option in self.options_to_save:
            option_obj, option_name = option

            if type(option_obj) is wx.CheckBox:
                options[option_name] = option_obj.IsChecked()
            elif type(option_obj) is wx.Choice:
                options[option_name] = option_obj.StringSelection
            elif type(option_obj) is wx.Slider:
                options[option_name] = option_obj.GetValue()
            else:
                raise ValueError(f"unhandled type of option {type(option_obj)} to save")

        logging.debug(f"saving options: {options}")

        with open("config/settings.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(options, indent=4, sort_keys=True))


    def load_options(self):
        if (Path("config") / "settings.json").exists():
            with open(Path("config") / "settings.json", encoding="utf-8") as f:
                options = json.loads(f.read())

        for option in self.options_to_save:
            option_obj, option_name = option

            if option_name in options:
                opt_value = options[option_name]

                if type(option_obj) is wx.CheckBox:
                    option_obj.SetValue(opt_value)
                elif type(option_obj) is wx.Choice:
                    option_obj.Select(option[0].Items.index(opt_value))
                elif type(option_obj) is wx.Slider:
                    option_obj.SetValue(opt_value)
                else:
                    raise ValueError(f"unhandled type of option {type(option_obj)} to load")

        self.change_intensity(None)
        self.change_russian_chance(None)
        self.change_device(None)

    def on_close(self, _):
        self.save_options()
        self.Destroy()

    def impulse(self, reason):
        # If the user has hit start
        if self.armed:
            if self.randomize_intensity_checkbox.IsChecked():
                intensity = random.randint(1, self.max_intensity_slider.GetValue())
            else:
                intensity = self.max_intensity_slider.GetValue()

            shock = False

            if self.russian_enable_checkbox.IsChecked():
                roll = random.randint(1, 100)
                if roll < self.russian_chance_slider.GetValue():
                    shock = True
            else:
                if not self.test_mode_checkbox.IsChecked():
                    shock = True

            if shock:
                self.device.shock(intensity, 1)
                logging.info(f"Shocked user with intensity {intensity} from {reason}")
            else:
                self.device.vibrate(intensity, 1)
                logging.info(f"Vibrated user with intensity {intensity} from {reason}")

    def on_death(self):
        if self.shock_on_death_checkbox.IsChecked():
            self.impulse("death")

    def on_hit(self):
        if self.shock_on_hit_checkbox.IsChecked():
            self.impulse("hit")

    def change_intensity(self, _):
        self.max_intensity_label.SetLabel(f"{self.max_intensity_slider.GetValue()}%")
        self.randomize_intensity_checkbox.SetLabel(f"Randomize intensity from 1% to {self.max_intensity_slider.GetValue()}%")

    def change_russian_chance(self, _):
        self.russian_shock_label.SetLabel(f"{self.russian_chance_slider.GetValue()}% Shock")
        self.russian_vibrate_label.SetLabel(f"{100 - self.russian_chance_slider.GetValue()}% Vibrate")

    def arm_zap(self, _):
        if self.start_button.GetLabel() == "Start":
            self.armed = True
            self.start_button.SetLabel("Stop")

            for option in self.shock_options:
                option.Disable()
        else:
            self.armed = False
            self.start_button.SetLabel("Start")

            for option in self.shock_options:
                option.Enable()

    def import_settings(self):
        # TODO: change all UI from settings
        pass

    def configure_csgo(self, _):
        csgo.configure_gse()
        self.configure_csgo_button.SetLabel("CS:GO Configured")
        self.configure_csgo_button.Disable()

    def change_device(self, _):
        self.device_config = load_device_config(self.device_change_dropdown.StringSelection)

    def configure_device(self, _):
        current_device = device_map[self.device_change_dropdown.StringSelection]

        for config_option in current_device.config_options:
            if current_device.config_options[config_option][1] is str:
                current_value = ""
                if config_option in self.device_config:
                    current_value = self.device_config[config_option]

                dlg = wx.TextEntryDialog(self, f"Enter option {config_option}:", value=current_value)
                if dlg.ShowModal() == wx.ID_OK:
                    self.device_config[config_option] = dlg.GetValue()
            elif current_device.config_options[config_option][1] is bool:
                dlg = wx.MessageDialog(self, f"{config_option}, yes or no?", style=wx.YES_NO)
                if dlg.ShowModal() == wx.ID_YES:
                    self.device_config[config_option] = True
                else:
                    self.device_config[config_option] = False

        save_device_config(self.device_change_dropdown.StringSelection, self.device_config)

    def device_connect(self, _):
        if self.connect_button.GetLabel() == "Connect":
            try:
                try:
                    self.device = device_map[self.device_change_dropdown.StringSelection](self.device_config)
                except TimeoutError:
                    wx.MessageDialog(self, "Failed to connect", style=wx.ICON_ERROR).ShowModal()
                    logging.error(f"{self.device_change_dropdown.StringSelection} failed to connect")

                self.device.vibrate(50, 1)

                self.device_configure_button.Disable()
                self.device_change_dropdown.Disable()
                self.start_button.Enable()
                self.connect_button.SetLabel("Disconnect")
            except TEMSError as e:
                wx.MessageDialog(self, str(e), f"Error from {self.device_change_dropdown.StringSelection}", style=wx.ICON_ERROR).ShowModal()
        else:
            self.device = None

            self.device_configure_button.Enable()
            self.device_change_dropdown.Enable()
            self.start_button.Disable()
            self.connect_button.SetLabel("Connect")



# GUI Setup

app = wx.App()
frame = PavShockHandler(None)

if csgo.check_gse():
    frame.configure_csgo_button.SetLabel("CS:GO Configured")
    frame.configure_csgo_button.Disable()

frame.Show()


app.MainLoop()

