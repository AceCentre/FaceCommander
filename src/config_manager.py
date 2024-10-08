# Standard library imports.
#
import copy
import logging
import time
import tkinter as tk
#
# JSON module.
# https://docs.python.org/3/library/json.html
import json
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Module for high-level file operations.
# https://docs.python.org/3/library/shutil.html
import shutil
#
# Local imports.
#
from src.app import App
from src.singleton_meta import Singleton
from src.utils.Trigger import Trigger

CURRENT_PROFILE_FILENAME = "current.json"
CURSOR_FILENAME = "cursor.json"
MOUSE_FILENAME = "mouse_bindings.json"
FILENAME = "keyboard_bindings.json"
BACKUP_PROFILE = "default"

logger = logging.getLogger("ConfigManager")

class ConfigManager(metaclass=Singleton):

    def __init__(self):
        logger.info("Initialising ConfigManager singleton.")
        self._currentProfilePath = None
        self._profileNames = None

        self.tempBindings = None
        self.tempMouseBindings = None
        self.tempConfig = None
        self.bindings = None
        self.mouse_bindings = None
        self.cursor_control = False
        self.unsave_configs = False
        self.unsave_mouse_bindings = False
        self.unsave_bindings = False
        self.throttle_time = 1.5
        self.config = None

        # Load config
        self.currentProfileDirectory = None
        self.current_profile_name = tk.StringVar()
        self.is_started = False
    
    @property
    def currentProfilePath(self):
        if self._currentProfilePath is None:
            self._currentProfilePath = Path(
                App().profilesDirectory, CURRENT_PROFILE_FILENAME)
        return self._currentProfilePath
    
    def set_throttle_time(self, time):
        self.throttle_time = time
    
    def get_throttle_time(self):
        return self.throttle_time
    
    def _get_profiles_directory(self, *name):
        path = App().profilesDirectory
        if path.exists():
            if not path.is_dir():
                raise RuntimeError(
                    "Non-directory found where profiles directory is expected."
                    f' {path}')
        else:
            logger.info(
                "Creating profiles directory by copying built-in profiles."
                f' Profiles directory "{path}".'
                f' Built-in profiles "{App().builtInProfilesDirectory}".')
            shutil.copytree(App().builtInProfilesDirectory, path)
        return Path(path, *name)

    def start(self):
        if not self.is_started:
            logger.info("Start ConfigManager singleton")
            loaded = None
            try:
                with self.currentProfilePath.open() as file:
                    self.load_profile(json.load(file)["default"])
                loaded = True
            except Exception as exception:
                loaded = False
                logging.error(exception)
            if not loaded:
                logging.error(
                    "Failed to load profile named in"
                    f' "{self.currentProfilePath}".')
                for name in self.profileNames:
                    try:
                        self.load_profile(name)
                        loaded = True
                        logging.error(f'Loaded profile as fall-back "{name}".')
                        break
                    except Exception as exception:
                        logging.error(exception)
                        logging.error(
                            f'Failed to fall back to profile "{name}".')
            if not loaded:
                raise RuntimeError("Failed to load any profile.")
            self.is_started = True

    @property
    def profileNames(self):
        if self._profileNames is None:
            self._profileNames = tuple(
                child.name for child in self._get_profiles_directory().iterdir()
                if child.is_dir()
            )
            logger.info(f'Profiles discovered {self._profileNames}.')
        return self._profileNames

    def remove_profile(self, name):
        logger.info(f'Remove profile "{name}".')
        shutil.rmtree(self._get_profiles_directory(name))
        # Next line will force the getter to rediscover profiles.
        self._profileNames = None
        logger.info(f"Remaining profiles {self.profileNames}.")

    def add_profile(self):
        # Random name base on local timestamp
        name = "profile_z" + str(hex(int(time.time() * 1000)))[2:]
        logger.info(f'Adding profile "{name}".')
        shutil.copytree(
            self._get_profiles_directory(BACKUP_PROFILE),
            self._get_profiles_directory(name)
        )
        # Next line will force the getter to rediscover profiles.
        self._profileNames = None
        logger.info(f"Profiles after addition {self.profileNames}.")

    def rename_profile(self, oldName, newName):
        logger.info(f'Rename "{oldName}" to "{newName}".')
        (self._get_profiles_directory(oldName)).rename(
            self._get_profiles_directory(newName)
        )
        # Next line will force the getter to rediscover profiles.
        self._profileNames = None
        logger.info(f"Profiles after rename {self.profileNames}.")

        if self.current_profile_name.get() == oldName:
            self.current_profile_name.set(newName)

    def load_profile(self, name: str):
        profileDirectory = self._get_profiles_directory(name)
        logger.info(f'Loading profile from "{profileDirectory}"')

        cursorPath = profileDirectory / CURSOR_FILENAME
        mousePath =  profileDirectory / MOUSE_FILENAME
        bindingPath = profileDirectory / FILENAME
        missing = tuple(
            path for path in (cursorPath, mousePath, bindingPath)
            if not path.is_file()
        )
        if len(missing) > 0:
            logger.critical(f'Configuration is invalid "{name}".')
            for path in missing:
                logger.critical(f'Missing configuration file "{path}".')
            raise FileNotFoundError(missing)

        # Load cursor config
        with cursorPath.open() as file:
            self.config = json.load(file)

        # Load mouse bindings
        with mousePath.open() as file:
            self.mouse_bindings = json.load(file)

        # Load keyboard bindings
        with bindingPath.open() as file:
            self.bindings = json.load(file)

        self.tempConfig = copy.deepcopy(self.config)
        self.tempMouseBindings = copy.deepcopy(self.mouse_bindings)
        self.tempBindings = copy.deepcopy(self.bindings)

        self.currentProfileDirectory = profileDirectory
        self.current_profile_name.set(name)

    def switch_profile(self, name: str):
        logger.info(f'Switching to profile "{name}"')
        self.load_profile(name)
        with self.currentProfilePath.open("w") as file:
            json.dump({"default": name}, file)

    # ------------------------------- BASIC CONFIG ------------------------------- #

    def set_temp_config(self, field: str, value):
        logger.info(f"Setting {field} to {value}")
        self.tempConfig[field] = value
        self.unsave_configs = True

    def write_config_file(self):
        cursorPath = Path(self.currentProfileDirectory, CURSOR_FILENAME)
        logger.info(f"Writing config file {cursorPath}")
        with cursorPath.open('w') as file:
            json.dump(self.config, file, indent=4, separators=(', ', ': '))

    def apply_config(self):
        logger.info("Applying config")
        self.config = copy.deepcopy(self.tempConfig)
        self.write_config_file()
        self.unsave_configs = False

    # ------------------------------ MOUSE BINDINGS CONFIG ----------------------------- #

    def set_temp_mouse_binding(self, gesture, device: str, action: str,
                               threshold: float, trigger: Trigger, time_threshold: float):

        logger.info(
            "setting keybind for gesture: %s, device: %s, key: %s, threshold: %s, trigger: %s",
            gesture, device, action, threshold, trigger.value)

        # Remove duplicate keybindings
        self.remove_temp_mouse_binding(device, action)

        # Assign
        self.tempMouseBindings[gesture] = [
            device, action, float(threshold), trigger.value, time_threshold
        ]
        self.unsave_mouse_bindings = True

    def remove_temp_mouse_binding(self, device: str, action: str):
        logger.info(
            f"remove_temp_mouse_binding for device: {device}, key: {action}")
        out_keybindings = {}
        for key, vals in self.tempMouseBindings.items():
            if (device == vals[0]) and (action == vals[1]):
                continue
            out_keybindings[key] = vals
        self.tempMouseBindings = out_keybindings
        self.unsave_mouse_bindings = True

    def apply_mouse_bindings(self):
        logger.info("Applying keybindings")
        self.mouse_bindings = copy.deepcopy(self.tempMouseBindings)
        self.write_mouse_bindings_file()
        self.unsave_mouse_bindings = False

    def write_mouse_bindings_file(self):
        mousePath = Path(self.currentProfileDirectory, MOUSE_FILENAME)
        logger.info(f"Writing keybindings file {mousePath}")

        with mousePath.open('w') as file:
            out_json = dict(sorted(self.mouse_bindings.items()))
            json.dump(out_json, file, indent=4, separators=(', ', ': '))

    # ------------------------------ KEYBOARD BINDINGS CONFIG ----------------------------- #

    def set_temp_binding(self, device: str, key_action: str,
                                  gesture: str, threshold: float,
                                  trigger: Trigger, time_threshold: float):
        logger.info(
            "setting keybind for gesture: %s, device: %s, key: %s, threshold: %s, trigger: %s, timer-threshold: %s",
            gesture, device, key_action, threshold, trigger.value, time_threshold)

        # Remove duplicate keybindings
        self.remove_temp_binding(device, key_action, gesture)

        # Assign
        self.tempBindings[gesture] = [
            device, key_action,
            float(threshold), trigger.value, time_threshold
        ]
        self.unsave_bindings = True

    def remove_temp_binding(self,
                            device: str,
                            key_action: str = "None",
                            gesture: str = "None"):
        """Remove binding from config by providing either key_action or gesture.
        """

        logger.info(
            f"remove_temp_binding for device: {device}, key: {key_action} or gesture {gesture}"
        )

        out_bindings = {}
        for ges, vals in self.tempBindings.items():
            if gesture == ges:
                continue
            if key_action == vals[1]:
                continue

            out_bindings[ges] = vals

        self.tempBindings = out_bindings

        self.unsave_bindings = True
        return

    def apply_bindings(self):
        logger.info("Applying bindings")

        self.bindings = copy.deepcopy(self.tempBindings)
        self.write_bindings_file()
        self.unsave_bindings = False

    def write_bindings_file(self):
        bindingPath = Path(self.currentProfileDirectory, FILENAME)
        logger.info(f"Writing bindings file {bindingPath}")

        with bindingPath.open('w') as file:
            out_json = dict(sorted(self.bindings.items()))
            json.dump(out_json, file, indent=4, separators=(', ', ': '))
    
    # ------------------------------Cursor Control Page-------------------------------------- #

    def set_cursor_control(self, status: bool):
        self.cursor_control = status

    def get_cursor_control(self):
        return self.cursor_control
    # ---------------------------------------------------------------------------- #
    def apply_all(self):
        self.apply_config()
        self.apply_mouse_bindings()
        self.apply_bindings()

    def destroy(self):
        logger.info("Destroy")
