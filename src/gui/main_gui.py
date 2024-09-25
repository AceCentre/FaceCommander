import logging
from PIL import Image
from src.config_manager import ConfigManager
from functools import partial
# Tk/Tcl module, only used for observable variables here.
# https://www.pythontutorial.net/tkinter/tkinter-stringvar/
from tkinter import IntVar, StringVar

import customtkinter

from src.app import App
from src.update_manager import UpdateManager
from src.gui import frames
from src.controllers import Keybinder
from src.gui.pages import (
    PageSelectCamera, PageKeyboard, PageAbout, PageSetting)

customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("assets/themes/google_theme.json")

logger = logging.getLogger("MainGUi")
PROF_DROP_SIZE = 220, 40
class MainGui:

    def __init__(self, tk_root):
        logger.info("Init MainGui")
        super().__init__()
        self.tk_root = tk_root

        # Get screen width and height for dynamic scaling
        screen_width = self.tk_root.winfo_screenwidth()
        screen_height = self.tk_root.winfo_screenheight()
        self.bounday_width = 800
        self.sidebar_big_size = 260
        self.sidebar_small_size = 60

        # Set window size based on screen dimensions for tablets
        if screen_width <= 1280:
            self.tk_root.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.9)}")
        else:
            self.tk_root.geometry("1024x800")

        self.tk_root.title(" ".join((App().name, App().version)))
        self.tk_root.iconbitmap("assets/images/icon.ico")
        self.tk_root.resizable(width=True, height=True)

        # Adjust scaling for higher-DPI displays
        self.tk_root.tk.call('tk', 'scaling', screen_width / 1280)

        # Configure rows and columns for grid responsiveness
        self.tk_root.grid_rowconfigure(1, weight=1)
        self.tk_root.grid_columnconfigure(1, weight=1)

        # Initialize observable variables
        self._updateState = None
        self.runningPublished = StringVar(self.tk_root, "")
        self.releasesSummary = StringVar(self.tk_root, "Update availability unknown.")
        self.installerSummary = StringVar(self.tk_root, "")
        self.installerPrompt = StringVar(self.tk_root, "")
        self.retrievingSize = IntVar(self.tk_root, 0)
        self.retrievedAmount = IntVar(self.tk_root, 0)

        # Create menu frame and assign callbacks
        self.frame_menu = frames.FrameMenu(self.tk_root,
                                           self.root_function_callback,
                                           height=360,
                                           width=self.sidebar_big_size,
                                           logger_name="frame_menu")
        self.frame_menu.grid(row=0, column=0, padx=0, pady=0, sticky="nsew", columnspan=1, rowspan=3)

        # Create Preview frame
        self.frame_preview = frames.FrameCamPreview(self.tk_root,
                                                    self.cam_preview_callback,
                                                    logger_name="frame_preview")
        self.frame_preview.grid(row=1, column=0, padx=0, pady=0, sticky="sew", columnspan=1)
        self.frame_preview.enter()
        
        if self.tk_root.winfo_width() < self.bounday_width:
            self.switch_profile_location("small")
            self.current_device_props = "small"
        else:
            self.switch_profile_location("big")
            self.current_device_props = "big"

        # Toggle switch
        self.toggle_switch = customtkinter.CTkSwitch(
            master=self.tk_root,
            text="Face Control",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=Keybinder().is_active,
            command=lambda: self.root_function_callback(
                "toggle_switch", {"switch_status": self.toggle_switch.get()}),
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
        self.toggle_switch.grid_remove()        
        self.pages = [
            PageSelectCamera(master=self.tk_root,),
            PageKeyboard(master=self.tk_root,),
            PageAbout(tkRoot=self.tk_root, updateHost=self),
            PageSetting(master=self.tk_root,)
        ]

        self.current_page_name = None
        self.pages[0].switch_raw_debug(self.current_device_props)
        for page in self.pages:
            page.grid(row=0, column=1, padx=5, pady=5, sticky="nsew", rowspan=2, columnspan=1)

        self.change_page(PageSelectCamera.__name__)

        # Profile UI
        self.frame_profile_switcher = frames.FrameProfileSwitcher(self.tk_root, main_gui_callback=self.root_function_callback)
        self.frame_profile_editor = frames.FrameProfileEditor(self.tk_root, main_gui_callback=self.root_function_callback)

        # # Make layout adjustments for responsiveness
        # self.adjust_layout_for_responsiveness()
        self.last_device_props = ''
        self.current_device_props = ''
        self.tk_root.bind("<Configure>", self.on_resize)

    def switch_profile_location(self, device_props):
        if device_props == "small":
            master = self.tk_root
            column= 1
        else:
            master = self.frame_menu
            column= 0
        try: self.profile_btn.grid_remove()
        except: pass
        prof_drop = customtkinter.CTkImage(
            Image.open("assets/images/prof_drop_head.png"), size=PROF_DROP_SIZE)
        
        self.profile_btn = customtkinter.CTkLabel(
            master=master,
            textvariable=ConfigManager().current_profile_name,
            image=prof_drop,
            height=42,
            compound="center",
            anchor="w",
            cursor="hand2",
            )         
        self.profile_btn.bind("<Button-1>",
                        partial(self.root_function_callback, "show_profile_switcher"))                   
        self.profile_btn.grid(row=0,
                            column=column,
                            padx=35,
                            pady=10,
                            ipadx=0,
                            ipady=0,
                            sticky="n",  # Center horizontally and align to the top
                            columnspan=2,  # Adjust this to span across multiple columns if needed
                            rowspan=1)

    def on_resize(self, event):
        """Print the current window size when resized."""
        window_width = self.tk_root.winfo_width()
        window_height = self.tk_root.winfo_height()
        # print(f"Window resized: {window_width}x{window_height}")
        
        if window_width < self.bounday_width :
            self.current_device_props = "small"
        else:
            self.current_device_props = "big"
        if self.current_device_props == "small" and self.last_device_props != "small":
            self.frame_menu.on_resize("small")
            self.frame_menu.configure(width=self.sidebar_small_size)
            self.frame_preview.grid_remove()
            self.toggle_switch.grid(row=1,
                                    column=1,
                                    padx=(100, 0),
                                    pady=0,
                                    sticky="n")    
            self.switch_profile_location("small")
            self.current_page_name = None
            self.pages[0].switch_raw_debug(self.current_device_props)
            for page in self.pages:
                page.grid(row=1, column=1, padx=5, pady=20, sticky="nsew", rowspan=2, columnspan=1)
            self.change_page(PageSelectCamera.__name__)
            self.last_device_props ="small"

        elif self.current_device_props != "small" and self.last_device_props == "small":
            self.frame_menu.on_resize("big")
            self.frame_menu.configure(width=self.sidebar_big_size)
            self.frame_preview.grid(row=1, column=0, padx=0, pady=0, sticky="sew", columnspan=1)
            self.toggle_switch.grid_remove() 
            self.switch_profile_location("big")
            self.current_page_name = None
            self.pages[0].switch_raw_debug(self.current_device_props)
            for page in self.pages:
                page.grid(row=0, column=1, padx=5, pady=5, sticky="nsew", rowspan=2, columnspan=1)    
            self.change_page(PageSelectCamera.__name__)
            self.last_device_props ="big" 

    def adjust_layout_for_responsiveness(self):
        """Adjust layout dynamically based on screen size."""
        self.tk_root.update_idletasks()

        screen_width = self.tk_root.winfo_screenwidth()

        # Adjust frame widths dynamically based on screen width
        if screen_width <= 1280:  # Adjust for tablet-sized screens
            self.frame_menu.configure(width=100)  # Use configure instead of config
            # self.frame_preview.configure(width=400)
        else:
            self.frame_menu.configure(width=260)
            # self.frame_preview.configure(width=600)

        # Update layout again
        self.tk_root.update_idletasks()

    def root_function_callback(self, function_name, args: dict = {}, **kwargs):
        logger.info(f"root_function_callback {function_name} with {args}")

        # Basic page navigate
        if function_name == "change_page":
            self.change_page(args["target"])
            self.frame_menu.set_tab_active(tab_name=args["target"])

        # Profiles
        elif function_name == "show_profile_switcher":
            self.frame_profile_switcher.enter()
        elif function_name == "show_profile_editor":
            self.frame_profile_editor.enter()

        elif function_name == "refresh_profiles":
            logger.info("refresh_profile")
            for page in self.pages:
                page.refresh_profile()

    def cam_preview_callback(self, function_name, args: dict, **kwargs):
        logger.info(f"cam_preview_callback {function_name} with {args}")

        if function_name == "toggle_switch":
            self.set_mediapipe_mouse_enable(new_state=args["switch_status"])

    def set_mediapipe_mouse_enable(self, new_state: bool):
        if new_state:
            Keybinder().set_active(True)
        else:
            Keybinder().set_active(False)

    def change_page(self, target_page_name: str):

        if self.current_page_name == target_page_name:
            return

        for page in self.pages:
            if page.__class__.__name__ == target_page_name:
                page.grid()
                page.enter()
                self.current_page_name = page.__class__.__name__

            else:
                page.grid_remove()
                page.leave()

    def poll_update_state(self):
        updateState = UpdateManager().state
        if self._updateState is None or updateState != self._updateState:
            logger.info(f"updateState {updateState}.")
            # It looks like the trace() callback gets invoked after every set
            # call, even if the value didn't change.
            if self.releasesSummary.get() != updateState.releasesSummary:
                self.releasesSummary.set(updateState.releasesSummary)
            if self.installerSummary.get() != updateState.installerSummary:
                self.installerSummary.set(updateState.installerSummary)
            if self.installerPrompt.get() != updateState.installerPrompt:
                self.installerPrompt.set(updateState.installerPrompt)
            if self.runningPublished.get() != updateState.runningPublished:
                self.runningPublished.set(updateState.runningPublished)
        self._updateState = updateState

    def del_main_gui(self):
        logger.info("Deleting MainGui instance")
        # try:
        self.frame_preview.leave()
        self.frame_preview.destroy()
        self.frame_menu.leave()
        self.frame_menu.destroy()
        for page in self.pages:
            page.leave()
            page.destroy()

        self.tk_root.quit()
        self.tk_root.destroy()