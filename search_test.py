import os
import sys
import argparse
import subprocess
import random
import concurrent.futures
from functools import partial
# Text stuff
import re
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import PyPDF2
import time
from html import escape

from pathlib import Path

from PyQt5 import QtGui
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import shutil

from tkinter import filedialog
from tkinter import Tk
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QSizeGrip

import json  
import datetime  

from main_window import Ui_MainWindow
from session_display import Ui_session_display

import resources_config_rc  
import sip

from send2trash import send2trash


from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QColorDialog, QWidget
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, show_main_window=False):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Reference Practice')
        self.session_schedule = {}
        # Install event filter
        self.installEventFilter(self)
        
        # Disable tab focus for all widgets
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.setFocusPolicy(QtCore.Qt.NoFocus)
        


        # Define default shortcuts
        self.default_shortcuts = {
            "main_window": {
                "start": "S", 
                "close": "Escape"
            },
            "session_window": {
                "toggle_highlight": "G",
                "toggle_text_field": "T",
                "color_window": "F1",
                "always_on_top": "A",
                "prev_sentence": "Left",
                "pause_timer": "Space",
                "close": "Escape",
                "next_sentence": "Right",
                "open_folder": "O",
                "copy_plain_text": "C",
                "copy_plain_text_metadata": "Ctrl+Shift+C",
                "copy_highlighted_text": "Ctrl+C",
                "copy_highlighted_text_metadata": "Shift+C",
                "toggle_autocopy": "F3",
                "toggle_metadata": "F2",
                "delete_sentence": "Ctrl+D",
                "zoom_in": "Q",
                "zoom_out": "D",
                "zoom_in_numpad": "+",
                "zoom_out_numpad": "-",
                "show_main_window": "Tab",
                "add_30_seconds": "Up",
                "add_60_seconds": "Ctrl+Up",
                "restart_timer": "Ctrl+Shift+Up"
            }
        }





        # Use the executable's directory for absolute paths
        if getattr(sys, 'frozen', False):  # Check if the application is frozen (compiled as an EXE)
            self.base_dir = os.path.dirname(sys.executable)
            self.app_path = sys.executable
            self.temp_dir = sys._MEIPASS
            
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.app_path = os.path.abspath(__file__)
            self.temp_dir = None



        self.presets_dir = os.path.join(self.base_dir, 'writing_presets')
        self.text_presets_dir = os.path.join(self.presets_dir, 'text_presets')
        self.session_presets_dir = os.path.join(self.presets_dir, 'session_presets')
        self.theme_presets_dir = os.path.join(self.presets_dir, 'theme_presets')  # New directory for themes
        self.default_themes_dir = os.path.join(self.base_dir,'default_themes')  # Default themes directory


        self.rainmeter_presets_dir = os.path.join(self.presets_dir,'rainmeter_presets')  
        self.rainmeter_files_dir = os.path.join(self.base_dir,'rainmeter_files')  
        self.rainmeter_deleted_files_dir = os.path.join(self.rainmeter_presets_dir,'Deleted Files') 


        self.default_themes = ['default_theme.txt','dark_theme.txt', 'light_theme.txt']
        self.current_theme = "default_theme.txt"

        print('------------------')
        print(' Base Directory:', self.base_dir)
        print(' Temporary Directory:', self.temp_dir)
        print(' Default Themes Directory:', self.default_themes_dir)
        print(' Theme Presets Directory:', self.theme_presets_dir)


        print(' Rainmeter Presets Directory:', self.rainmeter_presets_dir)
        print(' Rainmeter Files Directory:', self.rainmeter_files_dir)
        print(' Rainmeter Deleted Files Directory:', self.rainmeter_deleted_files_dir)

        print('------------------')


        self.create_directories()
        self.ensure_default_themes()

        
        # Initialize the randomize_settings variable or False depending on your default
        self.randomize_settings = True 
        self.autocopy_settings = False  
        self.auto_start_settings = False

        # Initialize cache variables
        self.sentence_names_cache = []
        self.session_names_cache = []


        self.sentence_selection_cache = -1
        self.session_selection_cache = -1

        # Init color settings
        self.color_settings = {}


        self.init_styles()
        

        self.table_sentences_selection.setItem(0, 0, QTableWidgetItem('112'))

        # Enable sorting on table headers
        self.table_sentences_selection.setSortingEnabled(True)
        self.table_session_selection.setSortingEnabled(True)


        # Alternative method (ensures interactivity)
        self.table_sentences_selection.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table_session_selection.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)


  


        self.load_presets()

        self.schedule = []
        self.total_time = 0
        self.selection = {'folders': [], 'files': []}

        self.KEYWORDS_TYPES = {}

        # Load session settings at startup
        self.load_session_settings()
        self.init_buttons()
        self.apply_shortcuts_main_window()


        # Hide the main window initially
        #self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)


        self.display = None  # Initialize with None
        # Automatically start the session if auto_start is True

        if self.auto_start_settings and (self.sentence_selection_cache >=0 and self.session_selection_cache >=0):
            
            self.start_session_from_files()
        # Show the main window if show_main_window is True
        elif show_main_window == True:
            self.show()

        # Initialize position for dragging
        self.oldPos = self.pos()
        self.init_styles()

    


    def init_message_boxes(self):
        """Initialize custom message box settings."""
        self.message_box = QtWidgets.QMessageBox(self)
        self.message_box.setIcon(QtWidgets.QMessageBox.NoIcon)  # Set to no icon by default
    
    def show_info_message(self, title, message):
        """Show an information message box without an icon."""
        self.message_box.setWindowTitle(title)
        self.message_box.setText(message)
        self.message_box.exec_()




    def ensure_default_themes(self):
        """Ensure default theme files are present in theme_presets_dir and replace any missing or corrupted files."""

        self.current_theme = 'default_theme.txt'
        # Determine the base directory based on whether the app is running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            temp_dir = sys._MEIPASS
            self.base_dir = os.path.dirname(sys.executable)
            self.default_themes_dir = os.path.join(temp_dir, 'default_themes')
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.default_themes_dir = os.path.join(self.base_dir, 'default_themes')

        # Ensure the theme presets directory exists
        os.makedirs(self.theme_presets_dir, exist_ok=True)

        for theme_file in self.default_themes:
            source_file = os.path.join(self.default_themes_dir, theme_file)
            destination_file = os.path.join(self.theme_presets_dir, theme_file)

            # If the destination file does not exist, or it's corrupted, replace it with the default theme
            if not os.path.exists(destination_file):
                self.copy_theme_file(source_file, destination_file)
            else:
                try:
                    # Check if the existing file is readable and not corrupted
                    with open(destination_file, 'r') as dst:
                        content = dst.read()
                        if not content.strip():
                            print(f"{theme_file} is empty or corrupted. Replacing with default.")
                            self.copy_theme_file(source_file, destination_file)
                except Exception as e:
                    print(f"Error reading {theme_file}: {e}. Replacing with default.")
                    self.copy_theme_file(source_file, destination_file)

    def copy_theme_file(self, source_file, destination_file):
        """Copy a theme file from source to destination."""
        if os.path.exists(source_file):
            try:
                with open(source_file, 'r') as src:
                    content = src.read()

                with open(destination_file, 'w') as dst:
                    dst.write(content)

                print(f"Copied {source_file} to {destination_file}")
            except Exception as e:
                print(f"Error copying {source_file} to {destination_file}: {e}")
        else:
            print(f"Source theme file {source_file} does not exist.")


    def reset_default_themes(self):
        """Replace corrupted or missing theme files in theme_presets_dir with default ones."""

        self.current_theme = 'default_theme.txt'
        # Determine the base directory based on whether the app is running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            temp_dir = sys._MEIPASS
            self.base_dir = self.base_dir = os.path.dirname(sys.executable)
            self.default_themes_dir = os.path.join(temp_dir, 'default_themes')
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.default_themes_dir = os.path.join(self.base_dir, 'default_themes')


        for theme_file in self.default_themes:
            source_file = os.path.join(self.default_themes_dir, theme_file)
            destination_file = os.path.join(self.theme_presets_dir, theme_file)
            
            # Remove the existing file if it exists
            if os.path.exists(destination_file):
                os.remove(destination_file)
            
            # Read from the source file and write to the destination file
            if os.path.exists(source_file):
                try:
                    with open(source_file, 'r') as src:
                        content = src.read()

                    with open(destination_file, 'w') as dst:
                        dst.write(content)

                    print(f"THEME RESTAURED : Replaced {theme_file} in {self.theme_presets_dir}")
                    self.init_styles()
                    

                except Exception as e:
                    print(f"Error copying {theme_file}: {e}")
            else:
                print(f"Source theme file {source_file} does not exist.")
        self.show_info_message( 'Invalid theme', f'Invalid theme file, theme restaured to default.')







    def showEvent(self, event):
        """Override showEvent to control window visibility."""
        if not self.isVisible():
            event.ignore()  # Ignore the event to keep the window hidden
        else:
            super().showEvent(event)  # Otherwise, handle normally

    def init_buttons(self):
        # Buttons for selection
        self.add_folders_button.clicked.connect(self.create_preset)
        self.delete_sentences_preset.clicked.connect(self.delete_sentences_files)
        
        # Buttons for preset
        self.save_session_presets_button.clicked.connect(self.save_session_presets) 
        self.delete_session_preset.clicked.connect(self.delete_presets_files)

        self.open_preset_button.clicked.connect(self.open_preset) 

        # Buttons for rainmeter
        self.rainmeter_preset_button.clicked.connect(self.create_rainmeter_preset) 

        # Start session button with tooltip
        self.start_session_button.clicked.connect(self.start_session_from_files)
        self.start_session_button.setToolTip(f"[{self.shortcut_settings['main_window']['start']}] Start the session.")

        # Close window button with tooltip
        self.close_window_button.clicked.connect(self.save_session_settings)
        self.close_window_button.clicked.connect(self.close)
        self.close_window_button.setToolTip(f"[{self.shortcut_settings['main_window']['close']}] Close the setting window.")

        # Toggles
        self.randomize_toggle.stateChanged.connect(self.update_randomize_settings)
        self.autocopy_toggle.stateChanged.connect(self.update_autocopy_settings)
        self.auto_start_toggle.stateChanged.connect(self.update_auto_start_settings)

        # Table selection handlers
        self.table_sentences_selection.itemChanged.connect(self.rename_presets)
        self.table_session_selection.itemChanged.connect(self.rename_presets)

        # Theme selector button
        self.theme_options_button.clicked.connect(self.open_theme_selector)

        # Preset search
        self.search_preset.textChanged.connect(self.filter_presets)




    def init_styles(self, dialog=None, dialog_color=None, session=None):
        """
        Initialize custom styles for various UI elements including buttons, spin boxes,
        table widgets, checkboxes, dialogs, and the main window. Optionally apply styles
        to a specific dialog or session window.
        """

        # Load the selected theme file
        selected_theme_path = os.path.join(self.theme_presets_dir, self.current_theme)
        print('NOW LOADING THEME : ',selected_theme_path)
        if selected_theme_path:
            try:
                with open(selected_theme_path, 'r') as f:
                    theme_styles = f.read()
            except FileNotFoundError:
                print("No theme selected or theme file not found. Applying default styles.")
                self.ensure_default_themes()
                return

            try:
                # Parse theme styles as JSON
                styles_dict = json.loads(theme_styles)

                # Apply styles to each element based on the keys in the theme file
                for element_group, element_styles in styles_dict.items():
                    # Split group of elements (comma-separated)
                    element_names = [name.strip() for name in element_group.split(',')]

                    for element_name in element_names:
                        if hasattr(self, element_name):
                            element = getattr(self, element_name)
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            element.setStyleSheet(style_sheet)

                        elif element_name == "MainWindow":
                            # Apply style directly to the MainWindow
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                if selector == "window_icon":
                                    if self.temp_dir : 
                                        file_path = os.path.join(self.temp_dir, style)
                                    else: 
                                        file_path = os.path.join(self.base_dir, style)
                                        print(file_path)
                                    self.setWindowIcon(QtGui.QIcon(file_path))
                                elif selector == "icon":
                                    if self.temp_dir : 
                                        file_path = os.path.join(self.temp_dir, style)
                                    else: 
                                        file_path = os.path.join(self.base_dir, style)
                                    self.label.setText(f"<html><head/><body><p><img src=\"{file_path}\"/></p></body></html>")
                                else:
                                    style_sheet += f"{selector} {{{style}}}\n"

                            self.setStyleSheet(style_sheet)
                            self.init_message_boxes()
                        elif dialog and element_name == "dialog_styles":
                            # Apply styles to the dialog if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            dialog.setStyleSheet(style_sheet)

                        elif dialog_color and element_name == "ColorPickerDialog":
                            print(element_styles.items())
                            # Apply styles specifically to ColorPickerDialog
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"

                            dialog_color.setStyleSheet(style_sheet)


                        elif session and element_name == "session_display":
                            # Apply style to session_display if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                if selector == "window_icon":
                                    if self.temp_dir : 
                                        file_path = os.path.join(self.temp_dir, style)
                                    else: 
                                        file_path = os.path.join(self.base_dir, style)
                                    session.setWindowIcon(QtGui.QIcon(file_path))

                                style_sheet += f"{style}\n"
                            session.setStyleSheet(style_sheet)

                            if "background:" not in session.styleSheet():
                                print('No background color')
                                session.setStyleSheet("background: rgb(0,0,0)")

                        elif  element_name == "text_display":
                            if session:


                                # Apply style to text_display if it matches the name in the theme file
                                style_sheet = ""
                                
                                for selector, style in element_styles.items():
                                    if selector == "text_color":
                                        session.color_settings[selector]=style

                                    elif "highlight_color_" in selector:
                                        session.color_settings[selector] = style


                                    elif selector == "always_on_top_border":   
                                        session.color_settings["always_on_top_border"]=style
                                    elif "metadata_" in selector:   
                                        session.color_settings[selector]=style
                                    else:
                                        style_sheet += f"{selector} {{{style}}}\n"
                                    if hasattr(session, 'text_display'):
                                        session.text_display.setStyleSheet(style_sheet)
                            else:

                                # Apply style to text_display if it matches the name in the theme file
                                style_sheet = ""
                                
                                for selector, style in element_styles.items():
                                    if selector == "text_color":
                                        self.color_settings[selector]=style

                                    elif "highlight_color_" in selector:
                                        self.color_settings[selector] = style


                        elif session and element_name == "lineEdit":
                            # Apply style to text_display if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            if hasattr(session, 'lineEdit'):
                                session.lineEdit.setStyleSheet(style_sheet)

                        elif session and element_name == "session_display_labels":
                            session_display_label_styles = styles_dict["session_display_labels"]
                            for label_name in ["session_info", "timer_display"]:
                                if hasattr(session, label_name):
                                    label = getattr(session, label_name)
                                    style_sheet = ""
                                    for selector, style in session_display_label_styles.items():
                                        style_sheet += f"{selector} {{{style}}}\n"
                                    label.setStyleSheet(style_sheet)

                # Apply font settings to session labels only if specified
                if session and "label_fonts" in styles_dict:
                    font_settings = styles_dict["label_fonts"]
                    font = QtGui.QFont()
                    font.setFamily(font_settings.get("family", "Arial"))
                    font.setPointSize(font_settings.get("size", 10))
                    font.setBold(font_settings.get("bold", False))
                    font.setItalic(font_settings.get("italic", False))
                    font.setWeight(font_settings.get("weight", 50))

                    # Apply font only to session labels
                    for label_name in ["session_info", "timer_display"]:
                        if hasattr(session, label_name):
                            label = getattr(session, label_name)
                            label.setFont(font)

                # Apply common button styles to QPushButton widgets
                if "common_button_styles" in styles_dict:
                    button_styles = styles_dict["common_button_styles"]
                    for button_name in ["theme_options_button", "add_folders_button", "delete_sentences_preset", "open_preset_button","rainmeter_preset_button",
                                        "delete_session_preset", "save_session_presets_button", "start_session_button", "close_window_button"]:
                        if hasattr(self, button_name):
                            button = getattr(self, button_name)
                            style_sheet = ""
                            for selector, style in button_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            button.setStyleSheet(style_sheet)

                # Apply styles to other elements if needed
                if "labels" in styles_dict:
                    label_styles = styles_dict["labels"]
                    for label_name in ["select_images", "label_7", "image_amount_label","sentence_amount_label", "duration_label", "label_5", "label_6"]:
                        if hasattr(self, label_name):
                            label = getattr(self, label_name)
                            style_sheet = ""
                            for selector, style in label_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            label.setStyleSheet(style_sheet)

                if "common_spinbox_styles" in styles_dict:
                    spinbox_styles = styles_dict["common_spinbox_styles"]
                    for spinbox_name in ["set_seconds", "set_number_of_sentences", "set_minutes"]:
                        if hasattr(self, spinbox_name):
                            spinbox = getattr(self, spinbox_name)
                            style_sheet = ""
                            for selector, style in spinbox_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            spinbox.setStyleSheet(style_sheet)

                if "common_checkbox_styles" in styles_dict:
                    checkbox_styles = styles_dict["common_checkbox_styles"]
                    style_sheet = ""
                    for selector, style in checkbox_styles.items():
                        style_sheet += f"{selector} {{{style}}}\n"
                    # Assuming self has checkboxes that need styling
                    for checkbox_name in ["auto_start_toggle", "randomize_toggle","autocopy_toggle"]:
                        if hasattr(self, checkbox_name):
                            checkbox = getattr(self, checkbox_name)
                            checkbox.setStyleSheet(style_sheet)

                if session and "session_buttons" in styles_dict:
                    button_styles = styles_dict["session_buttons"]
                    button_names = [
                        "grid_button", "toggle_highlight_button","color_text_button", "toggle_text_button",
                        "flip_horizontal_button", "flip_vertical_button",
                        "previous_sentence", "pause_timer", "stop_session",
                        "next_sentence", "copy_sentence_button", "clipboard_button","metadata_button",
                        "open_folder_button", "delete_sentence_button", "show_main_window_button"
                    ]
                    for button_name in button_names:
                        if hasattr(session, button_name):
                            button = getattr(session, button_name)
                            style_sheet = ""
                            for selector, style in button_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            button.setStyleSheet(style_sheet)

            except json.JSONDecodeError:
                print("Error parsing theme file. Applying default styles.")
                self.reset_default_themes()
        else:
            print("No theme selected or theme file not found. Applying default styles.")
            self.reset_default_themes()

        # Set item delegates and header settings for tables
        max_length_delegate = MaxLengthDelegate(max_length=60)
        self.table_sentences_selection.setItemDelegateForColumn(0, max_length_delegate)
        self.table_session_selection.setItemDelegateForColumn(0, max_length_delegate)

        # Prevent column resizing for table_sentences_selection
        header_images = self.table_sentences_selection.horizontalHeader()
        header_images.setSectionResizeMode(QHeaderView.Fixed)
        header_images.setSectionsClickable(True)  # Make header non-clickable

        # Prevent column resizing for table_session_selection
        header_session = self.table_session_selection.horizontalHeader()
        header_session.setSectionResizeMode(QHeaderView.Fixed)
        header_session.setSectionsClickable(True)  # Make header non-clickable

        # Ensure the selection behavior is correctly set after applying styles
        self.table_session_selection.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_session_selection.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)



    def update_selection_cache(self):
        """
        Initialize custom styles for the table widgets to change the selection color
        and customize the header appearance.
        """
        # Get the selected row
        selected_sentence_row = self.table_sentences_selection.currentRow()
        selected_preset_row = self.table_session_selection.currentRow()


        self.sentence_selection_cache = selected_sentence_row
        self.session_selection_cache = selected_preset_row

        print("cache selected_sentence_row", selected_sentence_row)
        print("cache session_selection_cache", selected_preset_row)



    def filter_presets(self):
        """Filter table_sentences_selection based on search_preset input."""
        search_text = self.search_preset.text().strip().lower()
        
        for row in range(self.table_sentences_selection.rowCount()):
            item = self.table_sentences_selection.item(row, 0)  # Assuming filenames are in column 0
            if item:
                filename = item.text().lower()
                self.table_sentences_selection.setRowHidden(row, search_text not in filename)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            # Custom Tab key handling
            if self.search_preset.hasFocus():
                # Clear focus from all widgets
                focused_widget = QtWidgets.QApplication.focusWidget()
                if focused_widget:
                    focused_widget.clearFocus()
                
                # Explicitly clear focus for the entire window
                self.clearFocus()
            else:
                # Set focus to search_preset
                self.search_preset.setFocus()
                self.search_preset.selectAll()
            
            # Prevent default Tab behavior
            event.accept()
            return
        
        # Call the parent class's keyPressEvent for other key events
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        # Optionally keep your existing event filter logic
        return super().eventFilter(obj, event)
