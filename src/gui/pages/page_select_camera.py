import logging
import tkinter

from src import utils
import customtkinter
from PIL import Image, ImageTk

from src.camera_manager import CameraManager
from src.config_manager import ConfigManager
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame

logger = logging.getLogger("PageSelectCamera")

CANVAS_WIDTH = 440
CANVAS_HEIGHT = 330

MAX_ROWS = 10


class PageSelectCamera(SafeDisposableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(MAX_ROWS, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Top text
        top_label = customtkinter.CTkLabel(master=self, text="Camera")
        top_label.cget("font").configure(size=24)
        top_label.grid(row=0,
                       column=0,
                       padx=20,
                       pady=20,
                       sticky="nw",
                       columnspan=2)

        # Label
        self.label = customtkinter.CTkLabel(master=self, text="Select a Camera")
        self.label.cget("font").configure(size=16, weight="bold")
        self.label.grid(row=1, column=0, padx=10, pady=(20, 10), sticky="nw")

        # Empty radio buttons
        self.radio_var = tkinter.IntVar(value=0)
        self.prev_radio_value = None
        self.radio_buttons = []

        # Camera canvas
        self.placeholder_im = Image.open(
            "assets/images/placeholder.png").resize(
                (CANVAS_WIDTH, CANVAS_HEIGHT))
        self.placeholder_im = ImageTk.PhotoImage(self.placeholder_im)
        self.canvas = tkinter.Canvas(master=self,
                                     width=CANVAS_WIDTH,
                                     height=CANVAS_HEIGHT)
        self.canvas.grid(row=1,
                         column=0,
                         padx=(10, 50),
                         pady=10,
                         sticky="e",
                         rowspan=MAX_ROWS)

        # Set first image.
        self.canvas_im = self.canvas.create_image(0,
                                                  0,
                                                  image=self.placeholder_im,
                                                  anchor=tkinter.NW)
        self.new_photo = None
        self.latest_camera_list = []

    def update_radio_buttons(self):
        """ Update radio_buttons to match CameraManager
        """
        new_camera_list = CameraManager().get_camera_list()
        if len(self.latest_camera_list) != len(new_camera_list):
            self.latest_camera_list = new_camera_list
            logger.info("Refresh radio_buttons")
            old_radios = self.radio_buttons

            logger.info(f"Get camera list {new_camera_list}")
            radio_buttons = []
            for row_i, cam_id in enumerate(new_camera_list):
                radio_text = f"Camera {cam_id}"

                cam_name = utils.get_camera_name(cam_id)
                if cam_name is not None:
                    radio_text = f"{radio_text}: {cam_name}"

                radio_button = customtkinter.CTkRadioButton(master=self,
                                                     text=radio_text,
                                                     command=self.radiobutton_event,
                                                     variable=self.radio_var,
                                                     value=cam_id)

                radio_button.grid(row=row_i + 2, column=0, padx=50, pady=10, sticky="w")
                radio_buttons.append(radio_button)

            # Set selected radio_button
            target_id = ConfigManager().config["camera_id"]
            self.radio_buttons = radio_buttons
            for radio_button in self.radio_buttons:
                if f"Camera {target_id}" == radio_button.cget("text"):
                    radio_button.select()
                    self.prev_radio_value = self.radio_var.get()
                    logger.info(f"Set initial camera to {target_id}")
                    break
            for old_radio in old_radios:
                old_radio.destroy()

    def radiobutton_event(self):
        # Open new camera.
        new_radio_value = self.radio_var.get()
        if new_radio_value == self.prev_radio_value:
            return
        logger.info(f"Change camera: {new_radio_value}")
        CameraManager().pick_camera(new_radio_value)
        ConfigManager().set_temp_config("camera_id", new_radio_value)
        ConfigManager().apply_config()
        self.prev_radio_value = new_radio_value

    def switch_raw_debug(self, device_props):
        self.device_props = device_props

    def page_loop(self):
        if self.is_destroyed:
            return

        if self.is_active:
            if self.device_props == "small":
                frame_rgb = CameraManager().get_debug_frame()
            else:
                frame_rgb = CameraManager().get_raw_frame()
            
            
            # Assign ref to avoid garbage collected
            self.new_photo = ImageTk.PhotoImage(
                image=Image.fromarray(frame_rgb).resize((CANVAS_WIDTH,
                                                         CANVAS_HEIGHT)))
            self.canvas.itemconfig(self.canvas_im, image=self.new_photo)
            self.canvas.update()
            
            CameraManager().thread_cameras.assign_done_flag.wait()
            self.update_radio_buttons()
            self.after(ConfigManager().config["tick_interval_ms"],
                       self.page_loop)

    def enter(self):
        super().enter()
        self.update_radio_buttons()
        self.after(1, self.page_loop)

    def refresh_profile(self):
        self.update_radio_buttons()
        new_camera_id = ConfigManager().config["camera_id"]
        CameraManager().pick_camera(new_camera_id)
