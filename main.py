import wx
from pavshock import PavShock
import csgo
from tems import Pavlok, PiShock, TEMSDevice, TEMSError, device_map
from pathlib import Path
import json
import random


# ZeusMate
# Zeus2
# ZeusIRL


def save_device_config(name, config):
    if not Path("config").is_dir():
        Path("config").mkdir()

    with open(Path("config") / f"{name}.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))


def load_device_config(name):
    fi = Path("config") / f"{name}.json"
    if fi.exists():
        with open(fi) as f:
            return json.loads(f.read())
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

    def impulse(self):
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
            else:
                self.device.vibrate(intensity, 1)

    def on_death(self):
        if self.shock_on_death_checkbox.IsChecked():
            self.impulse()

    def on_hit(self):
        if self.shock_on_hit_checkbox.IsChecked():
            self.impulse()

    def change_intensity(self, event):
        self.max_intensity_label.SetLabel(f"{event.Int}%")
        self.randomize_intensity_checkbox.SetLabel(f"Randomize intensity from 1% to {event.Int}%")

    def change_russian_chance( self, event ):
        self.russian_shock_label.SetLabel(f"{event.Int}% Shock")
        self.russian_vibrate_label.SetLabel(f"{100 - event.Int}% Vibrate")

    def arm_zap(self, event):
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

                self.device.vibrate(50, 1)

                # Save settings after we connect (Pavlok will save the MAC address)
                self.device_config = self.device.config
                save_device_config(self.device_change_dropdown.StringSelection, self.device_config)

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
