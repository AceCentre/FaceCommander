import customtkinter
from PIL import Image

ICON_SIZE = (40, 40)  # Adjust icon size as needed
ITEM_HEIGHT = 50  # Adjust item height as needed
LIGHT_BLUE = "#ADD8E6"  # Adjust color as needed
BUTTON_SPACING = 10  # Spacing between buttons


def mouse_in_widget(mouse_x, mouse_y, widget, expand_x=(0, 0), expand_y=(0, 0)):
    widget_x1 = widget.winfo_rootx() - expand_x[0]
    widget_y1 = widget.winfo_rooty() - expand_y[0]
    widget_x2 = widget_x1 + widget.winfo_width() + expand_x[0] + expand_x[1]
    widget_y2 = widget_y1 + widget.winfo_height() + expand_y[0] + expand_y[1]
    if mouse_x >= widget_x1 and mouse_x <= widget_x2 and mouse_y >= widget_y1 and mouse_y <= widget_y2:
        return True
    else:
        return False
    
class CustomDialog:
    def __init__(self, master, dropdown_items: dict, width, callback: callable):
        self.master = master
        self.dropdown_items = dropdown_items
        self.callback = callback
        self.width = width
        self.selected_gesture = list(dropdown_items.keys())[0]
        self.divs = {}
        self.max_columns = 4
        self.min_columns = 2

    def open(self, div_name):
        
        """Open the custom dialog as a modal popup using customtkinter."""
        self.dialog_window = customtkinter.CTkToplevel(self.master)
        self.dialog_window.title("Select an Option")
        self.dialog_window.resizable(True, True)

        # Center the dialog on the parent window
        self.center_window(self.dialog_window, self.width, 400)  # Adjust height as needed

        # Set dialog as modal
        self.dialog_window.grab_set()  # Block interaction with other windows
        self.dialog_window.focus_set()  # Focus the dialog window
        self.dialog_window.transient(self.master)  # Set it to be on top of the main window

        # Create a label
        label = customtkinter.CTkLabel(self.dialog_window, text="Select a Gesture", font=("Arial", 14))
        label.pack(pady=20)

        # Create a scrollable frame for items
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.dialog_window, width=self.width + 20)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create buttons for each item in dropdown_items using customtkinter
        for gesture, image_path in self.dropdown_items.items():
            image = customtkinter.CTkImage(Image.open(image_path).resize(ICON_SIZE), size=ICON_SIZE)
            btn = customtkinter.CTkButton(
                master=self.scrollable_frame,  # Add button to the scrollable frame
                text=gesture,
                image=image,
                width=self.width // self.max_columns - BUTTON_SPACING,
                height=ITEM_HEIGHT,
                border_width=0,
                corner_radius=0,
                fg_color=LIGHT_BLUE,
                hover_color="gray90",
                text_color_disabled="gray80",
                compound="left",
                anchor="w",
                command=lambda i=gesture: self.on_select(div_name, i)
            )
            self.divs[gesture] = {"button": btn, "image": image}
            # Initially place buttons in grid layout (4 columns)
            btn.grid(row=len(self.divs.items()) // self.max_columns, column=len(self.divs.items()) % self.max_columns, padx=5, pady=5, sticky="ew")

        # Close button
        close_button = customtkinter.CTkButton(self.dialog_window, text="Close", command=self.dialog_window.destroy)
        close_button.pack(pady=20)

        # Bind resize event to handle dialog size changes
        self.dialog_window.bind("<Configure>", self.on_resize)        

        # Wait for the dialog to be closed
        self.dialog_window.wait_window()  # Wait until this window is destroyed

    def center_window(self, window, width, height):
        """Center the window on the parent window."""
        # Get the parent's window position and size
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        # Calculate the position to center the dialog on the parent window
        x = parent_x + (parent_width // 4) - (width // 2)
        y = parent_y + (parent_height // 4) - (height // 2)

        # Set the geometry of the dialog to position it at (x, y)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def on_resize(self, event):
        """Handle window resize event."""
        dialog_width = self.dialog_window.winfo_width()

        # Determine the number of columns based on the dialog width
        if dialog_width > 900:
            num_columns = self.max_columns
        elif dialog_width > 700:
            num_columns = self.max_columns - 1
        elif dialog_width > 500:
            num_columns = self.max_columns - 2
        else:
            num_columns = 1
        
        # Update grid columns and reposition buttons
        self.update_grid(num_columns)

    def update_grid(self, num_columns):
        """Update the grid configuration and reposition buttons."""
        # Clear previous column configurations
        for i in range(self.max_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=0)

        # Reconfigure columns
        for i in range(num_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)
        
        # Reposition buttons
        for index, gesture in enumerate(self.divs):
            row = index // num_columns
            col = index % num_columns
            button = self.divs[gesture]['button']
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

    def on_select(self, div_name, selected_item):
        """Handle item selection and close the dialog."""
        self.callback(div_name, selected_item)  # Call the callback function with selected item
        self.dialog_window.destroy()  # Close the dialog after selection
