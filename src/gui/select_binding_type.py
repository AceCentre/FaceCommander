import customtkinter
from PIL import Image
from src.config_manager import ConfigManager
from tkinter import messagebox
import ctypes

ICON_SIZE = (40, 40)  # Adjust icon size as needed
IMAGE_SIZE = (100, 70)
ITEM_HEIGHT = 50  # Adjust item height as needed
LIGHT_BLUE = "#ADD8E6"  # Adjust color as needed
BUTTON_SPACING = 10  # Spacing between buttons
CONFIRM_BUTTON_COLOR = "#008CBA"  # Button color for modern look
CANCEL_BUTTON_COLOR = "#FF6347"  # Cancel button color
CONFIRM_ICON_PATH = "assets/images/confirm_icon.png"  # Path to the confirmation icon
DIV_WIDTH = 240

class Select_binding_type:
    def __init__(self, master, width, callback: callable):
        self.master = master
        self.callback = callback
        self.width = width

        # Load confirmation icon image
        self.confirm_icon = Image.open(CONFIRM_ICON_PATH).resize((20, 20))
        self.background_enabled_color = LIGHT_BLUE
        self.background_disabled_color = "#D3D3D3"  # Gray color for disabled state
        self.mouse_event = None
    def open(self):
        """Open the custom dialog as a modal popup using customtkinter."""
        self.dialog_window = customtkinter.CTkToplevel(self.master)
        self.dialog_window.title("Select binding type")
        self.dialog_window.resizable(True, True)

        # Center the dialog on the parent window
        self.center_window(self.dialog_window, self.width, 300)

        # Set dialog as modal
        self.dialog_window.grab_set()  # Block interaction with other windows
        self.dialog_window.focus_set()
        self.dialog_window.transient(self.master)

        button = customtkinter.CTkButton(
            master=self.dialog_window,
            text="Keyboard",
            command=lambda: self.confirm_selection('keyboard'),
            width=DIV_WIDTH,
            fg_color='lightblue'
        )

        button.pack(pady=(50, 20))

        mouse_event_list = ['Mouse left click', 'Mouse right click', 'Mouse pause / unpause', 'Reset cursor to center', 'Mouse middle click', 'Switch focus between monitors']
        self.mouse_event = customtkinter.CTkOptionMenu(master=self.dialog_window,
                                                       values=mouse_event_list,
                                                       width=DIV_WIDTH,
                                                       dynamic_resizing=False,
                                                       state="normal",
                                                       fg_color='gray95',
                                                       command=self.on_option_select
                                                       )
        self.mouse_event.pack(pady=(20, 50))
        # Create a frame for Confirm and Cancel buttons
        button_frame = customtkinter.CTkFrame(self.dialog_window, fg_color='gray95', border_color='gray95')
        button_frame.pack(pady=20)

        # Confirm button (initially disabled)
        self.confirm_button = customtkinter.CTkButton(
            button_frame, 
            text="Confirm", 
            command=lambda: self.confirm_selection('mouse'), 
            state="normal",  # Disabled until a gesture is selected
            fg_color=CONFIRM_BUTTON_COLOR
        )
        self.confirm_button.grid(row=0, column=0, padx=10)

        # Cancel button
        cancel_button = customtkinter.CTkButton(
            button_frame, 
            text="Cancel", 
            command=self.dialog_window.destroy, 
            fg_color=CANCEL_BUTTON_COLOR
        )
        cancel_button.grid(row=0, column=1, padx=10)

        # Wait for the dialog to be closed
        self.dialog_window.wait_window()
    def on_option_select(self, selected_value):
        for idx, (gesture_name, bind_info) in enumerate(ConfigManager().bindings.items()):
            type, key_action, thres, _, time_thres = bind_info
            if key_action.lower() in selected_value.lower() or selected_value == 'Switch focus between monitors' and key_action == 'cycle' :
                # Display a message or take some action to inform the user
                messagebox.showinfo("Binding type", "This mouse event already used")
                # Revert to the default or previous value
                self.mouse_event.set('Mouse left click')  # Set a default value
                return
        self.mouse_event = selected_value

    def center_window(self, window, width, height):
        """Center the window on the parent window."""
        
        hdc = ctypes.windll.user32.GetDC(0)
    
        # Get the screen DPI
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 is the LOGPIXELSX value for horizontal DPI
        
        # Release the device context (DC)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        
        # 96 DPI is the default for 100% scaling, so scaling is DPI / 96
        scaling_percentage = dpi_x / 96 * 100

        parent_x = int(self.master.winfo_rootx() * 100 / scaling_percentage)
        parent_y = int(self.master.winfo_rooty() * 100 / scaling_percentage)
        parent_width = int(self.master.winfo_width() * 100 / scaling_percentage)
        parent_height = int(self.master.winfo_height() * 100 / scaling_percentage)
        x = parent_x + (parent_width // 4) - (width // 2)
        y = parent_y + (parent_height // 4) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def confirm_selection(self, type):
        """Handle confirmation and close the dialog."""
        if type == 'mouse':
            event = self.mouse_event.get()
            if event == 'Mouse left click':
                key_action = 'left'
            if event == 'Mouse right click':
                key_action = 'right'
            if event == 'Mouse pause / unpause':
                key_action = 'pause'
                type = 'meta'
            if event == 'Reset cursor to center':
                key_action = 'reset'
                type = 'meta'
            if event == 'Mouse middle click':
                key_action = 'middle'
                type = 'meta'
            if event == 'Switch focus between monitors':
                key_action = 'cycle'
                type = 'meta'
            self.callback(type, key_action)
        else:
            self.callback(type, 'None')
        self.dialog_window.destroy()
