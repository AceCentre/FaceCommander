import tkinter

import customtkinter
from PIL import Image, ImageTk

from src.camera_manager import CameraManager
from src.config_manager import ConfigManager
from src.controllers import Keybinder
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import platform

CANVAS_WIDTH = 320
CANVAS_HEIGHT = 240
LIGHT_BLUE = "#F9FBFE"
TOGGLE_ICON_SIZE = (32, 20)
APP_NAME = 'FaceCommander'


class FrameCamPreview(SafeDisposableFrame):

    def __init__(self, master, master_callback: callable, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color=LIGHT_BLUE)

        self.minimize_var = None
        self.tk_root = master
        
        self.tray_icon = None
        threading.Thread(target=self.create_tray_icon, daemon=True).start()

        # Canvas.
        self.placeholder_im = Image.open("assets/images/placeholder.png")
        self.placeholder_im = ImageTk.PhotoImage(
            image=self.placeholder_im.resize((CANVAS_WIDTH, CANVAS_HEIGHT)))

        self.canvas = tkinter.Canvas(master=self,
                                     width=CANVAS_WIDTH,
                                     height=CANVAS_HEIGHT,
                                     bg=LIGHT_BLUE,
                                     bd=0,
                                     relief='ridge',
                                     highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky="sw")

        # Toggle label
        self.toggle_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Face control",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.toggle_label.cget("font").configure(size=14)
        self.toggle_label.grid(row=1,
                               column=0,
                               padx=(10, 0),
                               pady=5,
                               sticky="nw")

        # Toggle switch
        self.toggle_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=Keybinder().is_active,
            command=lambda: [
                master_callback("toggle_switch", {"switch_status": self.toggle_switch.get()}),
                self.face_control()
            ],
            onvalue=1,
            offvalue=0,
        )
        if ConfigManager().config["auto_play"]:
            self.toggle_switch.select()

        self.toggle_switch.grid(row=1,
                                column=0,
                                padx=(100, 0),
                                pady=5,
                                sticky="nw")
        
        # Toggle label
        self.minimize_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Minimize App",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.minimize_label.cget("font").configure(size=14)
        self.minimize_label.grid(row=1,
                               column=0,
                               padx=(10, 0),
                               pady=30,
                               sticky="nw")

        # Toggle switch
        self.minimize_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=self.minimize_var,
            command=lambda: [
                master_callback("minimize_switch", {"switch_status": self.minimize_switch.get()}),
                self.minimize_app()
            ],
            onvalue=1,
            offvalue=0,
        )

        self.minimize_switch.grid(row=1,
                                column=0,
                                padx=(100, 0),
                                pady=30,
                                sticky="nw")
        
        # Toggle description label
        self.toggle_label = customtkinter.CTkLabel(
            master=self,
            compound='right',
            text="Allow facial gestures to control\nyour actions. ",
            text_color="#444746",
            justify=tkinter.LEFT)
        self.toggle_label.cget("font").configure(size=12)
        self.toggle_label.grid(row=2,
                               column=0,
                               padx=(10, 0),
                               pady=5,
                               sticky="nw")

        # Set first image.
        self.canvas_image = self.canvas.create_image(0,
                                                     0,
                                                     image=self.placeholder_im,
                                                     anchor=tkinter.NW)
        self.new_photo = None
        self.after(1, self.camera_loop)

    def show_app(self):
        self.tk_root.deiconify()  # Show the main window
        Keybinder().set_active(False)

    def quit_app(self, icon, item):
        self.tray_icon.stop()  # Stop the tray icon
        self.tk_root.destroy()  # Close the app

    def create_tray_icon(self):
        # Create an image for the tray icon
        image = Image.open('assets/images/icon.ico')

        # Define the menu for the tray icon
        menu = Menu(
            MenuItem('Pause', lambda: self.show_app()),  # Show the app when clicked
            MenuItem('Quit', self.quit_app)  # Quit the app when clicked
        )

        # Create and run the tray icon
        self.tray_icon = Icon("CustomTkinter App", image, menu=menu)
        self.tray_icon.run()

    def minimize_app(self):
        self.minimize_var = not self.minimize_var
        if self.minimize_var and self.toggle_switch.get():
            self.tk_root.withdraw()
    
    def face_control(self):
        if self.minimize_var and self.toggle_switch.get():
            self.tk_root.withdraw()

    def camera_loop(self):
        if self.is_destroyed:
            return
        if self.is_active:
            if CameraManager().is_destroyed:
                return
            frame_rgb = CameraManager().get_debug_frame()
            # Assign ref to avoid garbage collected
            self.new_photo = ImageTk.PhotoImage(
                image=Image.fromarray(frame_rgb).resize((CANVAS_WIDTH,
                                                         CANVAS_HEIGHT)))
            self.canvas.itemconfig(self.canvas_image, image=self.new_photo)
            self.canvas.update()

            self.after(ConfigManager().config["tick_interval_ms"],
                       self.camera_loop)

    def enter(self):
        super().enter()
        self.after(1, self.camera_loop)

    def destroy(self):
        super().destroy()
