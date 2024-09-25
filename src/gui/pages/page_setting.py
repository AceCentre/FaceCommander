import logging
import tkinter
import customtkinter
import plistlib
import os
import sys
import winreg
import platform
from pathlib import Path
from tkinter import messagebox

APP_NAME = 'FaceCommander'
logger = logging.getLogger("PageSetting")

class PageSetting(customtkinter.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.os_type = platform.system()

        # Top label
        top_label = customtkinter.CTkLabel(master=self, text="Setting")
        top_label.cget("font").configure(size=24)
        top_label.grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        self.autostart_var = customtkinter.BooleanVar(value=self.check_autostart())
        # Toggle label
        self.auto_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Auto Start",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.auto_label.cget("font").configure(size=14)
        self.auto_label.grid(row=0,
                               column=0,
                               padx=(10, 0),
                               pady=60,
                               sticky="nw")

        # Toggle switch
        self.auto_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=self.autostart_var,
            command=self.toggle_autostart,
            onvalue=1,
            offvalue=0,
        )
    
        self.auto_switch.grid(row=0,
                                column=0,
                                padx=(100, 0),
                                pady=60,
                                sticky="nw")
        
    def add_to_registry(self):
        try:
            exe_path = os.path.abspath(sys.argv[0])
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to add to registry: {e}")
            return False

    def remove_from_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Failed to remove from registry: {e}")
            return False
        
    def add_to_launch_agents(self):
        plist = {
            'Label': 'com.yourapp.autostart',
            'ProgramArguments': [sys.executable, os.path.abspath(sys.argv[0])],
            'RunAtLoad': True,
            'KeepAlive': False,
        }
        launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents_dir / 'com.yourapp.autostart.plist'
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist, f)
        return True

    def remove_from_launch_agents(self):
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / 'com.yourapp.autostart.plist'
        if plist_path.exists():
            plist_path.unlink()
            return True
        return False

    def add_to_autostart(self):
        desktop_entry = f"""[Desktop Entry]
    Type=Application
    Exec={sys.executable} {os.path.abspath(sys.argv[0])}
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    Name=YourAppName
    Comment=Start YourAppName at login
    """
        autostart_dir = Path.home() / '.config' / 'autostart'
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / 'yourappname.desktop'
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
        return True

    def remove_from_autostart(self):
        desktop_file = Path.home() / '.config' / 'autostart' / 'yourappname.desktop'
        if desktop_file.exists():
            desktop_file.unlink()
            return True
        return False

    def check_autostart(self):
        if self.os_type == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Run",
                                     0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, APP_NAME)
                winreg.CloseKey(key)
                return True if value else False
            except FileNotFoundError:
                return False
            except ImportError:
                return False
        elif self.os_type == "Darwin":
            plist_path = Path.home() / 'Library' / 'LaunchAgents' / 'com.yourapp.autostart.plist'
            return plist_path.exists()
        elif self.os_type == "Linux":
            desktop_file = Path.home() / '.config' / 'autostart' / 'yourappname.desktop'
            return desktop_file.exists()
        else:
            return False

    def toggle_autostart(self):
        if self.autostart_var.get():
            success = self.enable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will start automatically on restart")
            else:
                messagebox.showerror("Error", "Failed to enable auto-start.")
        else:
            success = self.disable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will not start automatically")
            else:
                messagebox.showerror("Error", "Failed to disable auto-start.")

    def enable_autostart(self):
        try:
            if self.os_type == "Windows":
                return self.add_to_registry()  # Or add_to_startup()
            elif self.os_type == "Darwin":
                return self.add_to_launch_agents()
            elif self.os_type == "Linux":
                return self.add_to_autostart()
            else:
                return False
        except Exception as e:
            print(f"Enable autostart failed: {e}")
            return False

    def disable_autostart(self):
        try:
            if self.os_type == "Windows":
                return self.remove_from_registry()  # Or remove_from_startup()
            elif self.os_type == "Darwin":
                return self.remove_from_launch_agents()
            elif self.os_type == "Linux":
                return self.remove_from_autostart()
            else:
                return False
        except Exception as e:
            print(f"Disable autostart failed: {e}")
            return False
        
    def leave(self):
        print('<Leave>')
    
    def enter(self):
        print('<Enter>')

if __name__ == "__main__":
    # Example usage:
    root = customtkinter.CTk()  # Create a window
    app = PageSetting(root)  # Create an instance of PageSetting
    app.pack(fill="both", expand=True)  # Add it to the window
    root.mainloop()  # Start the Tkinter event loop
