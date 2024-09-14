import customtkinter as tk
import taglib
import os
import logging
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from tkinter import ttk
import pymediainfo
import threading

class FileProcessor:
    def __init__(self, directory_path=None):
        """Initialize the file processor with an optional directory."""
        self.directory_path = directory_path
        self.media_files = []

    def load_files(self):
        """Load media files from the directory."""
        if not self.directory_path:
            logging.error("No directory path specified.")
            return

        try:
            self.media_files = []  # Clear the list before loading
            for file_name in os.listdir(self.directory_path):
                file_path = os.path.join(self.directory_path, file_name)
                # Filter for supported media file extensions
                if file_name.lower().endswith(('.mp3', '.mp4', '.flac', '.ogg', '.m4v')):
                    self.media_files.append(file_path)
            if self.media_files:
                logging.info(f"Loaded {len(self.media_files)} media files from {self.directory_path}")
            else:
                logging.info(f"No supported media files found in {self.directory_path}")
        except Exception as e:
            logging.error(f"Error loading files: {e}")

    def update_titles(self):
        """Update the title of each media file to match its filename."""
        if not self.media_files:
            logging.info("No media files loaded.")
            return

        for file_path in self.media_files:
            try:
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Check if it's an MKV file
                if file_path.lower().endswith('.mkv'):
                    # Use pymediainfo to read MKV file
                    media_info = pymediainfo.MediaInfo.parse(file_path)
                    logging.info(f"Metadata for {file_path}:")
                    for track in media_info.tracks:
                        if track.track_type == "General":
                            logging.info(f"Title: {track.title}")
                    # MKV metadata editing requires mkvpropedit or mkvtoolnix (not in this example)
                    logging.info(f"MKV file: '{file_name}' detected. Title can't be changed with pytaglib.")
                    continue  # Skip to next file
                    
                # For non-MKV files, use pytaglib
                media_file = taglib.File(file_path)
                media_file.tags["TITLE"] = [file_name]
                media_file.save()
                logging.info(f"Updated 'Title' to: {file_name} for file: {file_path}")
            except Exception as e:
                logging.error(f"Error updating title for {file_path}: {e}")

    def print_metadata(self):
        """Print metadata for all loaded media files."""
        if not self.media_files:
            logging.info("No media files loaded.")
            return

        for file_path in self.media_files:
            try:
                if file_path.lower().endswith('.mkv'):
                    media_info = pymediainfo.MediaInfo.parse(file_path)
                    logging.info(f"Metadata for {file_path}:")
                    for track in media_info.tracks:
                        if track.track_type == "General":
                            logging.info(f"Title: {track.title}")
                else:
                    media_file = taglib.File(file_path)
                    logging.info(f"Metadata for {file_path}:")
                    for tag, value in media_file.tags.items():
                        logging.info(f"{tag}: {value}")
            except Exception as e:
                logging.error(f"Error reading metadata for {file_path}: {e}")


class LeftFrame(tk.CTkFrame):
    def __init__(self, master, file_processor):
        super().__init__(master)

        self.file_processor = file_processor

        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((0,1,2), weight=0)

        # Folder path label
        self.folder_label = tk.CTkLabel(self, text="No folder selected", font=("Courier New", 12))
        self.folder_label.grid(row=1, column=0, padx=10, pady=(5,5), sticky="nesw")

        # Add widgets
        self.select_button = tk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.select_button.grid(row=0, column=0, padx=5,pady=(5,5), sticky="nesw")

        self.update_button = tk.CTkButton(self, text="Process Files", command=self.run_update_titles)
        self.update_button.grid(row=2, column=0, padx=5, pady=(5,5), sticky="nesw")

    def select_folder(self):
        # Open a dialog to select the folder.
        folder_path = fd.askdirectory()
        if folder_path:
            self.file_processor.directory_path = folder_path
            self.file_processor.load_files()
            self.folder_label.configure(text=f"Selected Folder: {folder_path}")

    def run_update_titles(self):
        # Run the update_titles method in a separate thread.
        update_thread = threading.Thread(target=self.file_processor.update_titles)
        update_thread.start()


class RightFrame(tk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.log_box = tk.CTkTextbox(self, font=("Courier New", 12), height=200, activate_scrollbars=True)
        self.log_box.grid(row=0, column=0, padx=5, pady=(5,5), sticky="nesw")
        self.log_box.configure(state="disabled")
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Set up logging
        logging.basicConfig(level=logging.INFO, handlers=[self.TextHandler(self.log_box)])

    class TextHandler(logging.Handler):
        # A logging handler that writes logs to the Tkinter Textbox.
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            log_message = self.format(record)
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, log_message + '\n')
            self.text_widget.configure(state="disabled")
            self.text_widget.yview(tk.END)


class App(tk.CTk):
    def __init__(self, file_processor):
        super().__init__()

        self.title("Metadata Title Updater V0.0.1")
        self.geometry("600x400")
        self.centred_window(600, 400)
        self.resizable(False, False)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)


        self.file_processor = file_processor

        self.label = tk.CTkLabel(self, text="Metadata Title Updater", font=("", 28, "underline", "bold"))
        self.label.grid(row=0, column=0, padx=5, pady=(5,5), sticky="nws")

        # Create layout
        self.left_frame = LeftFrame(self, file_processor)
        self.left_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nesw")

        self.right_frame = RightFrame(self)
        self.right_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nesw", rowspan=2)

    def centred_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == "__main__":
    # Instantiate FileProcessor
    file_processor = FileProcessor()

    # Create the application and run it
    app = App(file_processor)
    app.mainloop()
