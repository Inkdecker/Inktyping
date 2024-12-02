import os
import sys
import subprocess
import random
import shelve

# Text stuff
import re
import codecs
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import PyPDF2
import time

from pathlib import Path
import cv2
import numpy as np
from pygame import mixer

from PyQt5 import QtGui
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import shutil

from tkinter import filedialog
from tkinter import Tk
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QSizeGrip

import json  # Add this import to use the json module
import datetime  # Import datetime for unique timestamp

from main_window import Ui_MainWindow
from session_display import Ui_session_display

import resources_config_rc  # This line should match your generated resource file name
import sip

from send2trash import send2trash



class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, show_main_window=False):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Reference Practice')
        self.session_schedule = {}


        # Define default shortcuts
        self.default_shortcuts = {
            "main_window": {
                "start": "S", 
                "close": "Escape"
            },
            "session_window": {
                "toggle_highlight": "G",
                "toggle_text_field": "T",
                "always_on_top": "A",
                "prev_sentence": "Left",
                "pause_timer": "Space",
                "close": "Escape",
                "next_sentence": "Right",
                "copy_plain_text": "C",
                "copy_highlighted_text": "Ctrl+C",
                "toggle_clipboard": "Shift+C",
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
            self.temp_dir = sys._MEIPASS
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.temp_dir = None



        self.presets_dir = os.path.join(self.base_dir, 'writing_presets')
        self.text_presets_dir = os.path.join(self.presets_dir, 'text_presets')
        self.session_presets_dir = os.path.join(self.presets_dir, 'session_presets')
        self.theme_presets_dir = os.path.join(self.presets_dir, 'theme_presets')  # New directory for themes
        self.default_themes_dir = os.path.join(self.base_dir,'default_themes')  # Default themes directory

        self.default_themes = ['default_theme.txt','dark_theme.txt', 'light_theme.txt']
        self.current_theme = "default_theme.txt"

        print('------------------')
        print(' Base Directory:', self.base_dir)
        print(' Temporary Directory:', self.temp_dir)
        print(' Default Themes Directory:', self.default_themes_dir)
        print(' Theme Presets Directory:', self.theme_presets_dir)
        print('------------------')


        self.create_directories()
        self.ensure_default_themes()

        
        # Initialize the randomize_settings variable or False depending on your default
        self.randomize_settings = True 
        self.clipboard_settings = False  
        self.auto_start_settings = False

        # Initialize cache variables
        self.sentence_names_cache = []
        self.session_names_cache = []


        self.sentence_selection_cache = -1
        self.session_selection_cache = -1


        self.init_styles()
        self.init_message_boxes()

        self.presets = {}  # This should be defined or loaded as needed

        self.table_sentences_selection.setItem(0, 0, QTableWidgetItem('112'))


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
        else:
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
        self.add_folders_button.clicked.connect(self.open_folder)
        self.delete_sentences_preset.clicked.connect(self.delete_sentences_files)
        
        # Buttons for preset
        self.save_session_presets_button.clicked.connect(self.save_session_presets) 
        self.delete_session_preset.clicked.connect(self.delete_presets_files)

        self.open_preset_button.clicked.connect(self.open_preset) 

        # Start session button with tooltip
        self.start_session_button.clicked.connect(self.start_session_from_files)
        self.start_session_button.setToolTip(f"[{self.shortcut_settings['main_window']['start']}] Start the session.")

        # Close window button with tooltip
        self.close_window_button.clicked.connect(self.save_session_settings)
        self.close_window_button.clicked.connect(self.close)
        self.close_window_button.setToolTip(f"[{self.shortcut_settings['main_window']['close']}] Close the setting window.")

        # Toggles
        self.randomize_toggle.stateChanged.connect(self.update_randomize_settings)
        self.clipboard_toggle.stateChanged.connect(self.update_clipboard_settings)
        self.auto_start_toggle.stateChanged.connect(self.update_auto_start_settings)

        # Table selection handlers
        self.table_sentences_selection.itemChanged.connect(self.rename_presets)
        self.table_session_selection.itemChanged.connect(self.rename_presets)

        # Theme selector button
        self.theme_options_button.clicked.connect(self.open_theme_selector)





    def init_styles(self, dialog=None, dialog_grid=None, session=None):
        """
        Initialize custom styles for various UI elements including buttons, spin boxes,
        table widgets, checkboxes, dialogs, and the main window. Optionally apply styles
        to a specific dialog or session window.
        """

        # Load the selected theme file
        selected_theme_path = os.path.join(self.theme_presets_dir, self.current_theme)
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

                        elif dialog and element_name == "dialog_styles":
                            # Apply styles to the dialog if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            dialog.setStyleSheet(style_sheet)

                        elif dialog_grid and element_name == "GridSettingsDialog":
                            # Apply styles specifically to GridSettingsDialog
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{selector} {{{style}}}\n"
                            dialog_grid.setStyleSheet(style_sheet)

                        elif session and element_name == "session_display":
                            # Apply style to session_display if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                style_sheet += f"{style}\n"
                            session.setStyleSheet(style_sheet)

                            if "background:" not in session.styleSheet():
                                print('No background color')
                                session.setStyleSheet("background: rgb(0,0,0)")

                        elif session and element_name == "text_display":
                            # Apply style to text_display if it matches the name in the theme file
                            style_sheet = ""
                            for selector, style in element_styles.items():
                                if selector == "highlight_names":
                                    session.highlight_names_settings=style
                                elif selector == "highlight_keywords":   
                                    session.highlight_keywords_settings=style
                                elif selector == "always_on_top_border":   
                                    session.always_on_top_borde_settings=style
                                else:
                                    style_sheet += f"{selector} {{{style}}}\n"
                                if hasattr(session, 'text_display'):
                                    session.text_display.setStyleSheet(style_sheet)

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
                    for button_name in ["theme_options_button", "add_folders_button", "delete_sentences_preset", "open_preset_button",
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
                    for checkbox_name in ["auto_start_toggle", "randomize_toggle","clipboard_toggle"]:
                        if hasattr(self, checkbox_name):
                            checkbox = getattr(self, checkbox_name)
                            checkbox.setStyleSheet(style_sheet)

                if session and "session_buttons" in styles_dict:
                    button_styles = styles_dict["session_buttons"]
                    button_names = [
                        "grid_button", "toggle_highlight_button", "toggle_text_button",
                        "flip_horizontal_button", "flip_vertical_button",
                        "previous_sentence", "pause_timer", "stop_session",
                        "next_sentence", "copy_sentence_button", "clipboard_button",
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
        header_images.setSectionsClickable(False)  # Make header non-clickable

        # Prevent column resizing for table_session_selection
        header_session = self.table_session_selection.horizontalHeader()
        header_session.setSectionResizeMode(QHeaderView.Fixed)
        header_session.setSectionsClickable(False)  # Make header non-clickable

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



    def open_folder(self):
        """
        Opens a dialog for folder selection, extracts keywords from user input, 
        and processes all EPUB, PDF, and TXT files within the selected folders.
        """
        self.update_selection_cache()
        preset_name = f'preset_{self.get_next_preset_number()}'
        dialog = MultiFolderSelector(self, preset_name)

        self.init_styles(dialog=dialog)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_dirs = dialog.get_selected_folders()
            keyword_input = dialog.get_keyword_input()  # Get the keyword input from user (already a list)
            highlight_keywords = dialog.get_highlight_keywords_option()
            output_option = dialog.get_output_option()  # Get output option

            preset_name = dialog.get_preset_name()  # Retrieve the preset name

            if not selected_dirs:
                self.show_info_message('No Selection', 'No folders were selected.')
                return

            # Prepare keywords from user input
            keywords = [kw for kw in keyword_input if not kw.startswith(';')]  # Extract valid keywords, ; used for comments

            # Process each selected directory
            for directory in selected_dirs:
                if os.path.isdir(directory):
                    # Process the folder with keywords, highlight option, and output option
                    self.process_epub_folder(directory, keywords, highlight_keywords, output_option, preset_name)

            self.show_info_message('Success', f'Processed all selected folders and saved to text_presets.')

        self.load_presets()





########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################


    def process_highlight_keywords(self, text, keywords):
        """Highlight all keywords based on their prefix while preserving the case in the original text."""
        modified_text = text  # Start with the original text
        for keyword in keywords:
            # Determine highlight style and behavior based on prefix

            if keyword.startswith('@'):
                base_keyword = keyword[1:]  # Remove '@' character
                highlight_style = "[|{}|]"  # Special character highlight
                extract = True  # Extract sentences containing this keyword
            elif keyword.startswith('#'):
                base_keyword = keyword[1:]  # Remove '#' character
                highlight_style = "[|{}|]"  # Character color highlight
                extract = False  # Do not extract sentences containing this keyword
            else:
                base_keyword = keyword  # Use the keyword as is
                highlight_style = "{{{}}}"  # Regular highlight
                extract = True  # Default to extracting sentences

            # Get the singular and plural forms for highlighting
            if keyword.startswith('@') or keyword.startswith('#'):
                keyword_forms = [base_keyword]  # Only the base keyword for '@' and '#'
            else:
                keyword_forms = self.get_keyword_forms(base_keyword)  # Get forms for other keywords

            # Highlight the keyword(s) in the text, preserving the original case
            for form in keyword_forms:
                # Use regex to find and highlight the keyword, preserving original capitalization
                pattern = re.compile(r'(?<!\w)({})\b'.format(re.escape(form)), re.IGNORECASE)

                # Lambda function to replace the matched word with highlighted style, preserving case
                def replace_func(match):
                    original_word = match.group(1)  # Get the exact match from the text
                    return highlight_style.format(original_word)  # Apply the original match with highlighting

                modified_text = pattern.sub(replace_func, modified_text)

        return modified_text


    def replace_broken_characters(self, text):
        replacements = {
            "“": '"',
            "’": "'",
            "”": '"',
            "—": "-",  # Correct long dash
            "â€“": "-",  # Misinterpreted en dash
            "â€”": "-",  # Misinterpreted em dash
            " ": "",  # Non-breaking space
            "…": "...",
            "‘": "'",
            "â€œ": '"',  # Misinterpreted opening double quote
            "â€": '"',   # Misinterpreted closing double quote or other symbols
            "â€™": "'",  # Misinterpreted apostrophe
            "–": "-",  # Replace en dash if present
        }

        # Create a pattern that matches any of the keys in replacements (sorted by length to handle multi-character sequences first)
        pattern = re.compile('|'.join(re.escape(key) for key in sorted(replacements.keys(), key=len, reverse=True)))

        # Function to replace all occurrences
        def replace(match):
            return replacements[match.group(0)]

        # Replace all occurrences of broken characters with their correct counterparts
        return pattern.sub(replace, text)





    def get_plural_form(self, keyword):
        if keyword.endswith('s'):
            return keyword  # Remove 's' for singular
        else:
            return keyword + 's'  # Add 's' for plural

    def get_singular_form(self, keyword):
        if keyword.endswith('s'):
            return keyword[:-1]  # Remove 's' for singular
        else:
            return keyword

    def get_keyword_forms(self, keyword):
        if keyword.startswith('&') or keyword.startswith('@'):
            keyword = keyword[1:]  # Remove the '&' character
            return [keyword]
        else:
            return [self.get_singular_form(keyword), self.get_plural_form(keyword)]

    def extract_sentences_with_keywords(self, file_path, keywords, combined_sentences):
        """
        Extract sentences containing the provided keywords from the file.
        Ensure each sentence is added only once, even if it contains multiple keywords.
        """
        def match_keywords(forms, sentence):
            """Check if any form of the keyword is found in the sentence."""
            for form in forms:
                if re.search(r'\b{}\b'.format(re.escape(form)), sentence, re.IGNORECASE):
                    return True
            return False

        # Load text from the file
        def extract_text_from_epub(file_path):
            book = epub.read_epub(file_path)
            full_text = ""
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                content = item.get_body_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                full_text += soup.get_text(separator=' ')
            return full_text

        # Load text depending on the file type
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                full_text = "".join([page.extract_text() or "" for page in reader.pages])
        elif file_path.endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    full_text = file.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='iso-8859-1') as file:
                    full_text = file.read()
        elif file_path.endswith('.epub'):
            full_text = extract_text_from_epub(file_path)
        else:
            print("Unsupported file type. Please select a PDF, text, or EPUB file.")
            return

        # Clean and split the text into sentences
        full_text = re.sub(r'\n(?=\S)', ' ', full_text)  # Handle newlines within paragraphs
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', full_text)  # Split by sentence endings

        # Maintain a set of unique sentences
        unique_sentences = set()

        # Iterate through each sentence and keyword
        for sentence in sentences:
            sentence_cleaned = self.replace_broken_characters(sentence.strip())  # Clean broken characters
            for keyword in keywords:
                # Get keyword forms (singular and plural)
                forms = self.get_keyword_forms(keyword)
                if match_keywords(forms, sentence_cleaned):
                    # Add the sentence to the unique set and break to avoid duplicate addition
                    if sentence_cleaned not in unique_sentences:
                        combined_sentences[keyword].append(sentence_cleaned)
                        unique_sentences.add(sentence_cleaned)
                    break  # Exit the keyword loop once the sentence is added

        print(f"Extracted {len(unique_sentences)} unique sentences.")

    def truncate_sentence(self, sentence, max_length=200):
            """Truncate the sentence at the last full word before exceeding the max length."""
            if len(sentence) <= max_length:
                return sentence
            words = sentence[:max_length].split()
            truncated_sentence = ' '.join(words[:-1]) + '...' if len(words) > 1 else words[0] + '...'
            return truncated_sentence

        # Truncate long sentences without cutting words
    def truncate_sentence_around_keyword(self, sentence, keyword, max_length=200, buffer=50):
        """
        Truncate the sentence around the keyword, ensuring the keyword is visible.
        max_length: Maximum length of the truncated sentence.
        buffer: How much text (in characters) to show before and after the keyword.
        """
        # Find where the keyword appears in the sentence (case-insensitive)
        match = re.search(r'\b{}\b'.format(re.escape(keyword)), sentence, re.IGNORECASE)

        if not match:
            # If the keyword is not found, truncate the sentence without cutting words
            return self.truncate_sentence(sentence, max_length)

        start_index = match.start()
        end_index = match.end()

        # Calculate where to start and end the truncation (ensure buffer is within bounds)
        start = max(0, start_index - buffer)
        end = min(len(sentence), end_index + buffer)

        # Ensure we do not cut the sentence in the middle of words
        # Adjust the start position to the nearest space after it (if it's not the beginning)
        if start > 0 and not sentence[start].isspace():
            start = sentence.rfind(' ', 0, start) + 1  # Move to the next word boundary

        # Adjust the end position to the nearest space before it (if it's not the end)
        if end < len(sentence) and not sentence[end - 1].isspace():
            end = sentence.rfind(' ', end)

        # Truncate the sentence with ellipses where necessary
        truncated_sentence = sentence[start:end]
        if start > 0:
            truncated_sentence = '...' + truncated_sentence
        if end < len(sentence):
            truncated_sentence = truncated_sentence + '...'

        return truncated_sentence
                            


    def process_epub_folder(self, folder_path, keywords, highlight_keywords, output_option, preset_name):
        """Process a folder of EPUB, PDF, or text files, extract sentences with user-provided keywords,
        highlight the keywords if requested, and save the results."""

        # Separate ignored keywords and process the rest
        ignored_keywords = [keyword for keyword in keywords if keyword.startswith('!')]
        keywords = [keyword for keyword in keywords if not keyword.startswith('!')]

        # Remove duplicates by converting the list of keywords to a set and back to a list
        keywords = list(set(keywords))
        print("Unique keywords:", keywords)

        # Dictionary to store sentences (using keywords with prefixes during search)
        combined_sentences = {keyword: [] for keyword in keywords}

        # Iterate through all files in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

            if os.path.isfile(file_path) and file_name.endswith(('.epub', '.pdf', '.txt')):  # Supported file formats
                # Extract sentences with keywords
                self.extract_sentences_with_keywords(file_path, keywords, combined_sentences)

        # Create new dictionary with filtered sentences (removing ignored keywords)
        filtered_sentences = {
            keyword.lstrip("&@#"): [
                sentence for sentence in sentences
                if not self.contains_ignored_keyword(sentence, ignored_keywords)
            ]
            for keyword, sentences in combined_sentences.items()
        }

        # Highlight keywords if requested after filtering ignored keywords
        if highlight_keywords:
            for keyword, sentences in filtered_sentences.items():
                for i in range(len(sentences)):
                    # Apply highlighting based on keyword prefix
                    sentences[i] = self.process_highlight_keywords(sentences[i], keywords)

        # Save results based on the output option
        output_file_path = os.path.join(self.text_presets_dir, f"{preset_name}.txt")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:  # Ensure UTF-8 encoding
            for sentences in filtered_sentences.values():
                output_file.write('\n\n'.join(sentences) + '\n\n')
        print(f"All sentences saved to {output_file_path}.")

        if output_option == "All output":
            # Save sentences into individual files for each keyword
            for keyword, sentences in filtered_sentences.items():
                if sentences:
                    output_file_path = os.path.join(self.text_presets_dir, f"{preset_name}_{keyword}.txt")
                    with open(output_file_path, 'w', encoding='utf-8') as output_file:  # Ensure UTF-8 encoding
                        output_file.write('\n\n'.join(sentences) + '\n\n')
            print(f"Sentences saved to individual files for each keyword.")



    def contains_ignored_keyword(self, sentence, ignored_keywords):
        for ignored_keyword in ignored_keywords:
            # Handle cases with both forms ignored or only plural ignored
            if ignored_keyword.startswith('!&'):
                # Ignore only the plural form
                base_ignored_keyword = ignored_keyword.lstrip('!&')
                forms_to_ignore = [base_ignored_keyword]  # Only plural form
            else:
                # Ignore both singular and plural forms
                base_ignored_keyword = ignored_keyword.lstrip('!')
                forms_to_ignore = self.get_keyword_forms(base_ignored_keyword)  # Both forms

            # Check if any form is present in the sentence
            for form in forms_to_ignore:
                if re.search(r'\b{}\b'.format(re.escape(form)), sentence, re.IGNORECASE):
                    return True
        return False         

########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################

    def get_next_preset_number(self):
        preset_files = [f for f in os.listdir(self.text_presets_dir) if f.startswith('preset_') and f.endswith('.txt')]
        existing_numbers = [int(f[len('preset_'):-len('.txt')]) for f in preset_files if f[len('preset_'):-len('.txt')].isdigit()]
        return max(existing_numbers, default=0) + 1



    def create_directories(self):
        # Create the directories if they do not exist
        os.makedirs(self.presets_dir, exist_ok=True)
        os.makedirs(self.text_presets_dir, exist_ok=True)
        os.makedirs(self.session_presets_dir, exist_ok=True)
        os.makedirs(self.theme_presets_dir, exist_ok=True)  # Create the theme presets directory
        print(f"Created directories: {self.presets_dir}, {self.text_presets_dir}, {self.session_presets_dir}, {self.theme_presets_dir}")


    def save_session_presets(self):
        """Saves session details into a separate text file for each session."""
        self.update_selection_cache()
        number_of_sentences = self.set_number_of_sentences.value()
        minutes = self.set_minutes.value()
        seconds = self.set_seconds.value()

        # Validate that number_of_sentences and duration are greater than 0
        if number_of_sentences <= 0 or (minutes <= 0 and seconds <= 0):
            self.show_info_message( 'Invalid Input', 'Number of sentences and duration must be greater than 0.')
            return

        # Create dictionary with session details
        session_data = {
            "session_name": "Session_1",  # Placeholder for session name, replace as needed
            "total_sentences": number_of_sentences,
            "time": f"{minutes}m {seconds}s"
        }


        # Check for existing preset files to determine the next available number
        files = os.listdir(self.session_presets_dir)
        preset_files = [f for f in files if f.startswith('session_presets_') and f.endswith('.txt')]
        
        # Extract numbers from filenames
        existing_numbers = []
        for filename in preset_files:
            try:
                number = int(filename.split('_')[-1].split('.')[0])
                existing_numbers.append(number)
            except ValueError:
                continue
        
        # Determine the next available number
        next_number = 1
        if existing_numbers:
            next_number = max(existing_numbers) + 1

        # Create the filename using the next available number
        session_preset_file = os.path.join(self.session_presets_dir, f'session_presets_{next_number}.txt')

        try:
            # Save dictionary to a new file in JSON format
            with open(session_preset_file, 'w') as file:
                json.dump(session_data, file)
            
            # Show success message
            print('Success',
                                                     f"Session Name: {session_data['session_name']}\n"
                                                     f"Total Sentences: {session_data['total_sentences']}\n"
                                                     f"Time: {session_data['time']}")

        except Exception as e:
            # Show error message if saving fails
            self.show_info_message('Error', f"Failed to save preset. Error: {str(e)}")

        
        # Save the preset
        self.load_presets()

        # Find the row with the new preset by its name
        preset_name = f'session_presets_{next_number}'  # This matches the name used for saving the preset
        rows = self.table_session_selection.rowCount()
        for row in range(rows):
            item = self.table_session_selection.item(row, 0)  # First column (Name)
            if item and item.text() == preset_name:
                self.table_session_selection.selectRow(row)
                break


    def delete_sentences_files(self):
        """Deletes the selected preset file and updates the preset table."""

        # Get the selected row
        selected_row = self.table_sentences_selection.currentRow()
        self.update_selection_cache()

  

        # Check if a row is actually selected
        if selected_row == -1:
            print('Warning', 'No preset selected for deletion.')
            return

        # Get the file name from the first column of the selected row
        file_item = self.table_sentences_selection.item(selected_row, 0)
        if not file_item:
            self.show_info_message('Warning', 'No file associated with the selected preset.')
            return

        file_name = file_item.text() + ".txt"
        file_path = os.path.join(self.text_presets_dir, file_name)

        # Delete the file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                # self.show_info_message( 'Success', f'Preset "{file_name}" deleted successfully.')
            except Exception as e:
                self.show_info_message('Error', f'Failed to delete preset. Error: {str(e)}')
                return
        else:
            self.show_info_message('Warning', f'File "{file_name}" does not exist.')


        # Reload the presets
        self.load_presets(use_cache=False)


    def delete_presets_files(self):
        """Deletes the selected preset file and updates the preset table."""
        # Get the selected row

        selected_row = self.table_session_selection.currentRow()
        self.update_selection_cache()

        # Check if a row is actually selected
        if selected_row == -1:
            print('Warning', 'No preset selected for deletion.')
            return
        
        # Get the file name from the first column of the selected row
        file_item = self.table_session_selection.item(selected_row, 0)
        if not file_item:
            self.show_info_message('Warning', 'No file associated with the selected preset.')
            return
        
        file_name = file_item.text() + ".txt"
        file_path = os.path.join(self.session_presets_dir, file_name)
        
        # Delete the file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                #self.show_info_message( 'Success', f'Preset "{file_name}" deleted successfully.')
            except Exception as e:
                self.show_info_message('Error', f'Failed to delete preset. Error: {str(e)}')
                return
        else:
            self.show_info_message('Warning', f'File "{file_name}" does not exist.')


        # Reload the presets
        self.load_presets(use_cache=False)


    def open_preset(self):
        """Open the selected preset file in the default text editor."""
        
        # Get the selected row
        selected_row = self.table_sentences_selection.currentRow()
        
        # Check if a row is actually selected
        if selected_row == -1:
            return

        # Get the file name from the first column of the selected row
        file_item = self.table_sentences_selection.item(selected_row, 0)
        if not file_item:
            self.show_info_message('Warning', 'No file associated with the selected preset.')
            return

        # Construct the full file name and path
        file_name = file_item.text() + ".txt"
        file_path = os.path.join(self.text_presets_dir, file_name)

        # Open the file if it exists
        if os.path.exists(file_path):
            try:
                # Open the file with the default text editor (Notepad)
                subprocess.Popen(['notepad.exe', file_path])
            except Exception as e:
                self.show_info_message('Error', f'Failed to open preset. Error: {str(e)}')
        else:
            self.show_info_message('Warning', f'File "{file_name}" does not exist.')


    def rename_presets(self, item):
        """Rename the preset file based on the new text typed in the row."""

        try:
            # Determine which table triggered the rename
            if item.tableWidget() == self.table_sentences_selection:
                cache = self.sentence_names_cache
                rename_directory = self.text_presets_dir
            elif item.tableWidget() == self.table_session_selection:
                cache = self.session_names_cache
                rename_directory = self.session_presets_dir
            else:
                # Unexpected table widget, exit early
                return
            row = item.row()
            if row >= len(cache):
                
                return

            # Get the old filename from the cache
            old_filename = cache[row]
            new_filename = item.text().strip() + ".txt"
            
            # Debugging output
            print(f"Row: {row}")
            print(f"Old filename: {old_filename}")
            print(f"New filename: {new_filename}")

            old_filepath = os.path.join(rename_directory, old_filename)
            new_filepath = os.path.join(rename_directory, new_filename)

            # Check if the old file exists
            if not os.path.exists(old_filepath):
                self.show_info_message('Error', f"Cannot rename: Original file '{old_filename}' does not exist.")
                self.load_presets(use_cache=False)  # Reload to revert to old name
                return

            # Check if the new filename already exists or if it is invalid
            if os.path.exists(new_filepath):
                self.show_info_message( 'Error', f"Cannot rename: '{new_filename}' already exists.")
                self.load_presets(use_cache=False)  # Reload to revert to old name
                return


            # Rename the file
            os.rename(old_filepath, new_filepath)
            #self.show_info_message( 'Success', f"Preset renamed successfully to {new_filename}")

            # Update the cache after renaming
            cache[row] = new_filename


        except Exception as e:
            self.show_info_message('Error', f"Failed to rename preset. Error: {str(e)}")
            self.load_presets(use_cache=True)  # Reload to revert to old name









    def load_presets(self, use_cache=False):
        """Load existing presets into the table by calling specific functions."""
        # Clear the tables and caches
        self.table_sentences_selection.setRowCount(0)
        self.table_session_selection.setRowCount(0)

        # Load sentence presets
        self.load_table_sentences_selection(use_cache)
        # Load session presets
        self.load_session_presets(use_cache)

        self.select_rows_from_cache(use_cache)

    def select_rows_from_cache(self, use_cache=False):
        """Select the previously selected rows from the cache after an action."""
        sentence_row = self.sentence_selection_cache
        session_row = self.session_selection_cache



        if sentence_row >= 0 and sentence_row < self.table_sentences_selection.rowCount():
            self.table_sentences_selection.selectRow(sentence_row)

        elif sentence_row >= 0 and sentence_row >= self.table_sentences_selection.rowCount():
            self.table_sentences_selection.selectRow(self.table_sentences_selection.rowCount()-1)


        if session_row >= 0 and session_row < self.table_session_selection.rowCount():
            self.table_session_selection.selectRow(session_row)

        elif session_row >= 0 and session_row >= self.table_session_selection.rowCount():
            self.table_session_selection.selectRow(self.table_session_selection.rowCount()-1)


    def load_table_sentences_selection(self, use_cache=False):
        """Load sentence preset files into the sentences presets table and update the cache, including a 'Sentences' column."""
        if use_cache:
            files = self.sentence_names_cache
        else:
            self.sentence_names_cache = []
            files = os.listdir(self.text_presets_dir)

        # Set up table with 2 columns: Name and Sentences
        self.table_sentences_selection.setColumnCount(2)
        self.table_sentences_selection.setHorizontalHeaderLabels(['Name', 'Sentences'])

        for filename in files:
            if filename.endswith(".txt"):
                # Prepare the display name (remove .txt)
                display_name = filename[:-4]  # Remove the last 4 characters (.txt)

                # Insert item into the sentence presets table
                row_position = self.table_sentences_selection.rowCount()
                self.table_sentences_selection.insertRow(row_position)

                # Add the display name
                name_item = QtWidgets.QTableWidgetItem(display_name)
                name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                self.table_sentences_selection.setItem(row_position, 0, name_item)

                # Count the number of empty lines in the text file
                empty_line_count = 0
                file_path = os.path.join(self.text_presets_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        if line.strip() == "":  # Check for empty line
                            empty_line_count += 1

                # Add the empty line count to the second column
                count_item = QtWidgets.QTableWidgetItem(str(empty_line_count))
                count_item.setTextAlignment(QtCore.Qt.AlignCenter)  # Center the text
                count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable

                self.table_sentences_selection.setItem(row_position, 1, count_item)

                # Update cache with the current filenames
                self.sentence_names_cache.append(filename)

        # Set column widths
        self.table_sentences_selection.setColumnWidth(0, 315)  # Adjust as needed
        self.table_sentences_selection.setColumnWidth(1, 80)   # Adjust as needed

    def load_session_presets(self, use_cache=False):
        """Load session preset files into the session presets table and update the cache, including 'Total' and 'Time' columns."""
        
        if use_cache:
            files = self.session_names_cache
        else:
            self.session_names_cache = []
            files = os.listdir(self.session_presets_dir)

        # Set up table with 3 columns: Name, Total, and Time
        self.table_session_selection.setColumnCount(3)
        self.table_session_selection.setHorizontalHeaderLabels(['Name', 'Sentences', 'Time'])

        # Set column widths
        self.table_session_selection.setColumnWidth(0, 360)  # Adjust as needed
        self.table_session_selection.setColumnWidth(1, 85)  # Adjust as needed
        self.table_session_selection.setColumnWidth(2, 100)  # Adjust as needed

        for filename in files:
            if filename.endswith(".txt"):
                # Prepare the display name (remove .txt)
                display_name = filename[:-4]  # Remove the last 4 characters (.txt)

                # Insert item into the session presets table
                row_position = self.table_session_selection.rowCount()
                self.table_session_selection.insertRow(row_position)

                # Add the display name
                name_item = QtWidgets.QTableWidgetItem(display_name)
                name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                self.table_session_selection.setItem(row_position, 0, name_item)

                # Load JSON data from the file
                file_path = os.path.join(self.session_presets_dir, filename)
                with open(file_path, 'r') as file:
                    try:
                        session_data = json.load(file)
                        total_sentences = session_data.get("total_sentences", 0)
                        time = session_data.get("time", "0m 0s")
                    except json.JSONDecodeError:
                        total_sentences = 0
                        time = "0m 0s"

                # Add the total sentences and time to the respective columns
                total_item = QtWidgets.QTableWidgetItem(str(total_sentences))
                total_item.setTextAlignment(QtCore.Qt.AlignCenter)  # Center the text
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable

                time_item = QtWidgets.QTableWidgetItem(time)
                time_item.setTextAlignment(QtCore.Qt.AlignCenter)  # Center the text
                time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable

                self.table_session_selection.setItem(row_position, 1, total_item)
                self.table_session_selection.setItem(row_position, 2, time_item)

                # Update cache with the current filenames
                self.session_names_cache.append(filename)




 
    def start_session_from_files(self):
        """
        Creates and runs SessionDisplay using information from the selected session and preset files.
        """

        # Helper function to convert time string to seconds
        def convert_time_to_seconds(time_str):
            minutes, seconds = 0, 0
            if 'm' in time_str:
                minutes = int(time_str.split('m')[0])
                time_str = time_str.split('m')[1].strip()
            if 's' in time_str:
                seconds = int(time_str.split('s')[0])
            return minutes * 60 + seconds

        # Initialize session data
        session_details = {}

        # Get the selected session preset file
        selected_session_row = self.table_session_selection.currentRow()
      
        # Validate the loaded data
        if selected_session_row == -1:
            print("No valid session details found.")
            self.show()
            print("Settings window opened")
            return

        selected_sentences = []  # Initialize selected sentences

        if selected_session_row != -1:
            # Fetch the session preset filename
            session_file_item = self.table_session_selection.item(selected_session_row, 0)

            if session_file_item:
                session_filename = session_file_item.text() + ".txt"
                session_file_path = os.path.join(self.session_presets_dir, session_filename)
                
                # Read session details from the session preset file
                try:
                    with open(session_file_path, 'r', encoding='utf-8') as f:  # Ensure UTF-8 encoding
                        session_details = json.load(f)
                        print(f"Loaded session details from {session_filename}: {session_details}")
                except (FileNotFoundError, json.JSONDecodeError):
                    print(f"Error reading session file: {session_filename}")
                    return

                # Get the selected sentence preset row
                selected_sentences_row = self.table_sentences_selection.currentRow()
                if selected_sentences_row == -1:
                    print("No valid sentence preset selected.")
                    return

                # Fetch the text file name from the sentences table
                text_file_item = self.table_sentences_selection.item(selected_sentences_row, 0)
                if text_file_item:
                    text_file_name = text_file_item.text() + ".txt"  # Append .txt
                    text_file_path = os.path.join(self.text_presets_dir, text_file_name)

                    # Read sentences from the text file
                    try:
                        with open(text_file_path, 'r', encoding='utf-8') as f:  # Ensure UTF-8 encoding
                            selected_sentences = [line.strip() for line in f.readlines() if line.strip()]
                            print(f"Loaded {len(selected_sentences)} sentences from {text_file_path}.")
                    except FileNotFoundError:
                        print(f"Text file not found: {text_file_path}")
                        return

        # Shuffle sentences if randomize_settings is True
        if self.randomize_settings:
            random.shuffle(selected_sentences)
            print("Sentences have been shuffled randomly.")

        # Convert the session time to seconds
        session_time = convert_time_to_seconds(session_details.get('time', '0m 0s'))

        # Use the total_sentences value from the session details
        total_sentences_to_display = session_details.get('total_sentences', len(selected_sentences))

        # Check if there are enough sentences to display
        if total_sentences_to_display > len(selected_sentences):
            print(f"Warning: Not enough sentences to display. Requested {total_sentences_to_display}, but only {len(selected_sentences)} available.")
            total_sentences_to_display = len(selected_sentences)

        # Select only the number of sentences specified by total_sentences
        selected_sentences = selected_sentences[:total_sentences_to_display]

        # Prepare session schedule and total sentences
        self.session_schedule = {
            0: [
                session_details.get('session_name', 'Session'),
                total_sentences_to_display,
                session_time
            ]
        }
        self.total_scheduled_sentences = total_sentences_to_display

        if self.display is not None:
            print("Closing the existing SessionDisplay instance.")
            self.display.close()  # Close the existing window
            self.display = None   # Reset the reference

        # Initialize and run SessionDisplay
        self.display = SessionDisplay(
            file_path=text_file_path,
            shortcuts=self.shortcut_settings,
            schedule=self.session_schedule,
            items=selected_sentences,  
            total=self.total_scheduled_sentences,
            clipboard_settings=self.clipboard_settings
        )
        self.init_styles(session=self.display)

        self.display.load_entry()
        self.display.show()

        self.save_session_settings()




    def load_session_settings(self):
        session_settings_path = os.path.join(self.presets_dir, 'session_settings.txt')

        # Default settings to be used if there's a problem with the file
        default_settings = {
            "selected_sentence_row": -1,
            "selected_session_row": -1,
            "randomize_settings": False,
            "auto_start_settings": False,
            "clipboard_settings": False,
            "theme_settings": 'default_theme.txt',
            "shortcuts": self.default_shortcuts
        }

        # Load current settings if the file exists
        if os.path.exists(session_settings_path):
            try:
                with open(session_settings_path, 'r') as f:
                    current_settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                current_settings = default_settings.copy()  # Fallback to default if there is an error
                print("Error loading session settings. Using default settings.")
        else:
            current_settings = default_settings.copy()  # Use default settings if the file doesn't exist
            print("Session settings file not found. Using default settings.")

        # Validate the shortcuts
        if not self.validate_shortcuts(current_settings.get('shortcuts', {})):
            print("Invalid shortcuts detected. Resetting to default shortcuts.")
            self.reset_shortcuts()  # Reset only the shortcuts to the default
            current_settings['shortcuts'] = self.default_shortcuts  # Ensure in-memory settings reflect the reset

        # Apply the valid or reset settings
        self.shortcut_settings = current_settings.get('shortcuts', self.default_shortcuts)
        self.randomize_settings = current_settings.get('randomize_settings', False)
        self.auto_start_settings = current_settings.get('auto_start_settings', False)
        self.clipboard_settings = current_settings.get('clipboard_settings', False)
        self.current_theme = current_settings.get('theme_settings', 'default_theme.txt')

        # Toggle the randomize and auto-start settings
        self.randomize_toggle.setChecked(self.randomize_settings)  # Toggle based on loaded value
        self.auto_start_toggle.setChecked(self.auto_start_settings)  # Toggle based on loaded value
        self.clipboard_toggle.setChecked(self.clipboard_settings)  # Toggle based on loaded value

        # --- Row selection logic ---
        selected_sentence_row = current_settings.get('selected_sentence_row', -1)
        selected_session_row = current_settings.get('selected_session_row', -1)

        # Ensure selected rows are within the table's bounds
        if 0 <= selected_sentence_row < self.table_sentences_selection.rowCount():
            self.table_sentences_selection.selectRow(selected_sentence_row)
        else:
            print("Invalid or out-of-bounds selected_sentence_row, no selection applied.")

        if 0 <= selected_session_row < self.table_session_selection.rowCount():
            self.table_session_selection.selectRow(selected_session_row)
        else:
            print("Invalid or out-of-bounds selected_session_row, no selection applied.")

        self.update_selection_cache()
        # Save the session settings after loading them (in case anything needs updating)
        self.save_session_settings()

    def save_session_settings(self):
        """Save the current session settings to the session_settings.txt file."""
        session_settings_path = os.path.join(self.presets_dir, 'session_settings.txt')

        # Collect the current settings
        current_settings = {
            "selected_sentence_row": self.table_sentences_selection.currentRow(),
            "selected_session_row": self.table_session_selection.currentRow(),
            "randomize_settings": self.randomize_settings,
            "auto_start_settings": self.auto_start_settings,
            "clipboard_settings": self.clipboard_settings,
            "theme_settings": self.current_theme,
            "shortcuts": self.shortcut_settings
        }

        # Save the settings to the file
        with open(session_settings_path, 'w') as f:
            json.dump(current_settings, f, indent=4)
        print("Session settings saved.")


    def validate_shortcuts(self, shortcuts):
        valid = True

        for window, actions in shortcuts.items():
            for action, shortcut in actions.items():
                try:
                    # Validate shortcut format
                    if len(shortcut) == 1 and shortcut.isalpha():
                        continue  # Single-letter shortcuts are allowed, skip validation

                    # Attempt to create a QKeySequence to validate the shortcut
                    sequence = QtGui.QKeySequence(shortcut)
                    if sequence.isEmpty():
                        raise ValueError("Invalid QKeySequence")
                    
                except Exception as e:
                    print(f"Invalid shortcut: {shortcut} for {window} - {str(e)}")
                    valid = False

        return valid

    def apply_shortcuts_main_window(self):
        """Apply the shortcuts for the main window."""

        self.main_window_start_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcut_settings["main_window"]["start"]), self)
        self.main_window_start_shortcut.activated.connect(self.start_session_from_files)

        self.main_window_close_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcut_settings["main_window"]["close"]), self)
        self.main_window_close_shortcut.activated.connect(self.close)

    def reset_shortcuts(self):
        # Path to session settings file
        session_settings_path = os.path.join(self.presets_dir, 'session_settings.txt')
        
        # Load current settings
        if os.path.exists(session_settings_path):
            try:
                with open(session_settings_path, 'r') as f:
                    current_settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                current_settings = {}
        else:
            current_settings = {}

        # Reset only the shortcuts
        current_settings['shortcuts'] = self.default_shortcuts

        # Write updated settings back to file
        with open(session_settings_path, 'w') as f:
            json.dump(current_settings, f, indent=4)
        
        print("Shortcuts reset to defaults.")


    def update_clipboard_settings(self, state):
        """Update the clipboard_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.clipboard_settings = True
        else:
            self.clipboard_settings = False

    def update_randomize_settings(self, state):
        """Update the randomize_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.randomize_settings = True
        else:
            self.randomize_settings = False

    def update_auto_start_settings(self, state):
        """Update the randomize_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.auto_start_settings = True
        else:
            self.auto_start_settings = False
        print(self.auto_start_settings)




    def grab_schedule(self):
        """Builds self.session_schedule with data from the schedule"""
        self.session_schedule = {}
        for row in range(self.table_session_selection.rowCount()):
            self.session_schedule[row] = []
            for column in range(self.table_session_selection.columnCount()):
                if self.table_session_selection.item(row, column).text() == '0':
                    pass
                self.session_schedule[row].append(self.table_session_selection.item(row, column).text())


    def open_theme_selector(self):
        """Open the theme selection dialog."""
        dialog = ThemeSelectorDialog(self, self.theme_presets_dir, self.current_theme)
        self.init_styles(dialog=dialog)
        if dialog.exec_():
            selected_theme = dialog.get_selected_theme()
            if selected_theme:
                self.current_theme = selected_theme
                self.save_session_settings()  # Save the updated theme setting

                self.init_styles() # Load the theme



class SessionDisplay(QWidget, Ui_session_display):
    closed = QtCore.pyqtSignal() # Needed here for close event to work.

    def __init__(self, file_path = None, shortcuts = None, schedule=None, items=None, total=None, clipboard_settings=None):
        super().__init__()
        self.setupUi(self)

        # Initialize grid state
        self.setWindowTitle('Practice')


        # Install event filter on the QLineEdit
        self.lineEdit.installEventFilter(self)


        # Initialize text settings dictionary with default values
        self.text_display_settings = {
            "font_size": 16,         # Default font size
            "font_family": "Arial",   # Default font family
            "font_weight": QtGui.QFont.Normal,  # Default font weight
            "font_color": "black",    # Default font color


            "font_size_lineedit": 30,  # Default font size
            "max_length_lineedit": 500  # Default max length

        }

        #Default highlights values
        self.highlight_names_settings = "color: rgb(237,183,76);font-weight: bold;"
        self.highlight_keywords_settings = "color: rgb(219,208,119);font-weight: bold;"
        self.always_on_top_borde_settings = "rgb(255, 0, 0)"

        self.text_display.setWordWrap(True)  # Enable word wrapping for the QLabel
        self.lineEdit.setMaxLength(self.text_display_settings["max_length_lineedit"])


        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # Create the border overlay QLabel
        self.border_overlay = QLabel(self)
        self.border_overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.border_overlay.setStyleSheet("background: transparent;")
        self.border_overlay.hide()  # Hide it initially

        self.init_sizing()
        self.init_scaling_size()
        self.schedule = schedule
        self.shortcuts = shortcuts
        self.file_path = file_path
        self.playlist = items
        self.playlist_position = 0

        self.text_toggle = True
        self.highlight_toggle = True
        self.init_timer()
        self.init_entries()
        self.installEventFilter(self)


        self.init_session_buttons()
        self.apply_shortcuts_session_window()
        self.skip_count = 1

        # Other initialization logic
        self.old_position = None  # Initialize old_position for dragging


        self.resizeEvent = self.update_border_overlay_geometry

        # Connect the resize event to update the border overlay
        self.setMinimumSize(QtCore.QSize(550, 200))
        self.clipboard_settings = clipboard_settings

    def resizeEvent(self, event):
        super(SessionDisplay, self).resizeEvent(event)
        # Adjust the grid overlay to match the new image size and position
        self.grid_overlay.setGeometry(self.image_display.geometry())
        
    def eventFilter(self, source, event):
        if source == self.lineEdit and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Backspace and event.modifiers() == QtCore.Qt.ShiftModifier:
                self.load_prev_sentence()  # Navigate to the previous sentence
                self.lineEdit.clear()  # Optionally clear the input field
                return True  # Indicate that the event has been handled
        return super().eventFilter(source, event)



    def mousePressEvent(self, event):
        """Capture the mouse press event to initiate dragging."""
        if event.button() == QtCore.Qt.LeftButton:
            self.old_position = event.globalPos()
        if not self.lineEdit.geometry().contains(event.pos()):
            self.lineEdit.clearFocus()  # Deselect the QLineEdit

    def mouseMoveEvent(self, event):
        """Handle the mouse movement for dragging the window."""
        if event.buttons() == QtCore.Qt.LeftButton and self.old_position:
            delta = event.globalPos() - self.old_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_position = event.globalPos()

    def mouseReleaseEvent(self, event):
        """Reset the dragging state after the mouse button is released."""
        if event.button() == QtCore.Qt.LeftButton:
            self.old_position = None

    def wheelEvent(self, event):
        # Check if Ctrl key is pressed
        ctrl_pressed = event.modifiers() & QtCore.Qt.ControlModifier

        if ctrl_pressed:
            # Rotate image based on wheel movement
            if event.angleDelta().y() > 0:
                self.rotate_image_right()
            else:
                self.rotate_image_left()
        else:
            # Zoom in or out based on wheel movement
            if event.angleDelta().y() > 0:
                self.zoom_plus()
            else:
                self.zoom_minus()


    def keyPressEvent(self, event):
        """Handle key press events for navigation and input."""
        # Check for Shift + Backspace
        if event.key() == Qt.Key_Backspace and event.modifiers() == Qt.ShiftModifier:
            self.load_prev_sentence()  # Logic to go to the previous sentence
            self.lineEdit.clear()  # Clear the text in the QLineEdit if desired
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.load_next_sentence()  # Logic to go to the next sentence
            self.lineEdit.clear()  # Clear the text in the QLineEdit
        else:
            super(SessionDisplay, self).keyPressEvent(event)  # Call base class method


    def copy_sentence(self, rich_text=True):
        """Copy the current sentence to the clipboard, with or without rich text."""
        # Retrieve the current sentence
        current_sentence = self.playlist[self.playlist_position].strip()

        if rich_text:
            # Extract color styles from the settings (Ensure proper extraction of RGB values)
            keyword_color = re.search(r"color:\s*rgb\((.*?)\)", self.highlight_keywords_settings)
            name_color = re.search(r"color:\s*rgb\((.*?)\)", self.highlight_names_settings)
            
            # Fallback colors if extraction fails
            keyword_color = [int(c) for c in keyword_color.group(1).split(",")] if keyword_color else [255, 165, 0]  # Default: orange
            name_color = [int(c) for c in name_color.group(1).split(",")] if name_color else [0, 0, 255]  # Default: blue

            # Prepare HTML-style formatting for rich text using inline CSS for color
            highlighted_sentence = re.sub(
                r'\{\s*(.*?)\s*\}', 
                fr'<span style="color:rgb({keyword_color[0]},{keyword_color[1]},{keyword_color[2]})">\1</span>',
                current_sentence
            )
            highlighted_sentence = re.sub(
                r'\[\|\s*(.*?)\s*\|\]', 
                fr'<span style="color:rgb({name_color[0]},{name_color[1]},{name_color[2]})">\1</span>',
                highlighted_sentence
            )

            # Create a mime data object with both plain text and HTML content
            clipboard = QApplication.clipboard()
            mime_data = QtCore.QMimeData()

            # Set the HTML content using inline CSS for the highlighting
            mime_data.setData('text/html', f"<p>{highlighted_sentence}</p>".encode('utf-8'))

            # Set the plain text content (without any brackets or highlights)
            plain_text = re.sub(r'\{\s*(.*?)\s*\}|\[\|\s*(.*?)\s*\|\]', r'\1\2', current_sentence)
            mime_data.setText(plain_text)

            # Set the mime data to the clipboard
            clipboard.setMimeData(mime_data)
            print(f"Copied Rich Text (HTML): <p>{highlighted_sentence}</p>")

        else:
            # For plain text, remove brackets and highlights
            clipboard_text = re.sub(r'\{\s*(.*?)\s*\}|\[\|\s*(.*?)\s*\|\]', r'\1\2', current_sentence)

            # Copy to clipboard as plain text (with no brackets or highlights)
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            print(f"Copied Plain Text: {clipboard_text}")




    def toggle_clipboard(self):
        if self.clipboard_settings:
            self.clipboard_settings = False
            self.clipboard_button.setChecked(False)
            print("Auto copy to clipboard : Off")
        else:
            self.clipboard_settings = True
            self.clipboard_button.setChecked(True)
            print("Auto copy to clipboard : On")




    def open_text_folder(self):
        # Retrieve the current preset path
        current_preset_path = os.path.normpath(self.file_path) 

        # Check if the preset path exists
        if os.path.exists(current_preset_path):

            # Using os.startfile to open the folder and select the preset
            subprocess.Popen(f'explorer /select,"{current_preset_path}"')
            print(f"Opened folder containing: {current_preset_path}")
        else:
            print("Preset path does not exist.")

    def sanitize_filename(self, filename):
        """
        Removes unusable characters from the filename by replacing them with underscores.
        """
        # Replace any character that is not alphanumeric or underscore with an underscore
        return re.sub(r'[^\w\s-]', '_', filename).strip()


    def remove_sentence(self):
        # Ensure the file exists
        if not os.path.exists(self.file_path):
            print("File path does not exist.")
            return

        # Read the current sentence to be removed
        current_sentence = self.playlist[self.playlist_position].strip()

        # Read the content of the file
        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        # Remove the current sentence from the file's content, including its corresponding empty line
        with open(self.file_path, 'w') as file:
            skip_next_line = False
            for i, line in enumerate(lines):
                # Skip the current sentence and the following empty line if present
                if skip_next_line:
                    skip_next_line = False
                    continue

                if line.strip() == current_sentence:
                    if i + 1 < len(lines) and lines[i + 1].strip() == "":  # Check if the next line is empty
                        skip_next_line = True  # Skip the next empty line
                    continue  # Skip the current sentence

                # Write the line back to the file if it's not the current sentence or its empty line
                file.write(line)

        # Remove the current sentence from the playlist
        self.playlist.pop(self.playlist_position)
        self.playlist_position -= 1

        # Create a unique filename for the deleted sentence file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        truncated_sentence = current_sentence[:30].replace(" ", "_")  # Limit to 30 chars and replace spaces
        sanitized_sentence = self.sanitize_filename(truncated_sentence)  # Sanitize the sentence for a valid filename
        unique_filename = f"{timestamp}_{sanitized_sentence}.txt"

        # Get the directory where the current file is located (from self.file_path)
        current_file_dir = os.path.dirname(self.file_path)

        # Define the path to the new file in the same folder as the main file
        new_file_path = os.path.join(current_file_dir, unique_filename)

        # Write the deleted sentence to the new text file
        with open(new_file_path, 'w') as new_file:
            new_file.write(current_sentence)

        # Send the newly created file to the recycle bin
        send2trash(new_file_path)

        # Load the next sentence in the playlist
        self.load_next_sentence()

        print(f"Sentence removed: '{current_sentence}' and saved to: '{new_file_path}' (sent to recycle bin)")





    def show_main_window(self):
        view.show()              # Show the main window
        view.raise_()            # Bring the window to the front
        view.activateWindow()    # Focus on the window

    def init_sizing(self):
        """
        Resizes the window to half of the current screen's resolution,
        sets states for window flags
        
        """
        self.resize(self.screen().availableSize() / 2)
        self.toggle_always_on_top_status = False
        self.frameless_status = False
        self.sizePolicy().setHeightForWidth(True)

    def init_scaling_size(self):
        """
        Creates a scaling box size that is used as a basis for
        label to scale off of. The box dimensions are determined by the 
        smallest side of half of the given rectangle from the
        current screen's available resolution.

        """
        half_screen = self.screen().availableSize() / 2
        min_length = min(half_screen.height(), half_screen.width())
        self.scaling_size = QtCore.QSize(min_length, min_length)

    def init_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.countdown)
        self.timer.start(500)

    def init_entries(self):
        self.entry = {
            'current': 0,
            'total': [*self.schedule][-1] + 1,
            'amount of items': int(self.schedule[0][1]),
            'time': int(self.schedule[0][2])}
        self.new_entry = True
        if self.entry['amount of items'] > 1:
            self.end_of_entry = False
        else:
            self.end_of_entry = True
        









    def init_session_buttons(self):
        # Session tools
        self.toggle_highlight_button.clicked.connect(self.toggle_highlight)
        self.toggle_highlight_button.setToolTip(f"[{self.shortcuts['session_window']['toggle_highlight']}] Toggle highlight")


        self.toggle_text_button.clicked.connect(self.toggle_text_field)
        self.toggle_text_button.setToolTip(f"[{self.shortcuts['session_window']['toggle_text_field']}] Toggle text field")


        # Session navigation
        self.previous_sentence.clicked.connect(self.load_prev_sentence)
        self.previous_sentence.setToolTip(f"[{self.shortcuts['session_window']['prev_sentence']}] Previous sentence")

        self.pause_timer.clicked.connect(self.pause)
        self.pause_timer.setToolTip(f"[{self.shortcuts['session_window']['pause_timer']}] Pause Timer")

        self.stop_session.clicked.connect(self.close)
        self.stop_session.setToolTip(f"[{self.shortcuts['session_window']['close']}] Stop Session and closes window")

        self.next_sentence.clicked.connect(self.load_next_sentence)
        self.next_sentence.setToolTip(f"[{self.shortcuts['session_window']['next_sentence']}] Next sentence")

        # Preset path and folder
        self.copy_sentence_button.clicked.connect(self.copy_sentence)
        self.copy_sentence_button.setToolTip(f"[{self.shortcuts['session_window']['copy_highlighted_text']}] Copy sentence to clipboard")

        self.clipboard_button.clicked.connect(self.toggle_clipboard)
        self.clipboard_button.setToolTip(f"[{self.shortcuts['session_window']['toggle_clipboard']}] Automatically copy current sentence to clipboard")



        self.open_folder_button.clicked.connect(self.open_text_folder)
        self.open_folder_button.setToolTip(f"[{self.shortcuts['session_window']['open_folder']}] Open preset folder")

        self.delete_sentence_button.clicked.connect(self.remove_sentence)
        self.delete_sentence_button.setToolTip(f"[{self.shortcuts['session_window']['delete_sentence']}] Delete sentence")

        # Setting window
        self.show_main_window_button.clicked.connect(self.show_main_window)
        self.show_main_window_button.setToolTip(f"[{self.shortcuts['session_window']['show_main_window']}] Open settings window")

        
        

        


    def apply_shortcuts_session_window(self):

        """Apply the shortcuts for the session window."""
        self.toggle_highlight_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_highlight"]), self)
        self.toggle_highlight_key.activated.connect(self.toggle_highlight)


        self.toggle_text_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_text_field"]), self)
        self.toggle_text_key.activated.connect(self.toggle_text_field)


        self.always_on_top_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["always_on_top"]), self)
        self.always_on_top_key.activated.connect(self.toggle_always_on_top)

        self.prev_sentence_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["prev_sentence"]), self)
        self.prev_sentence_key.activated.connect(self.load_prev_sentence)

        self.pause_timer_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["pause_timer"]), self)
        self.pause_timer_key.activated.connect(self.pause)

        self.close_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["close"]), self)
        self.close_key.activated.connect(self.close)

        self.next_sentence_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["next_sentence"]), self)
        self.next_sentence_key.activated.connect(self.load_next_sentence)

        self.open_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["open_folder"]), self)
        self.open_key.activated.connect(self.open_text_folder)

        # Shortcut for copying as rich text (Ctrl+C)
        self.copy_rich_text_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_plain_text"]), self)
        self.copy_rich_text_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=False))

        # Shortcut for copying as plain text (C)
        self.copy_plain_text_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_highlighted_text"]), self)
        self.copy_plain_text_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=True))

        self.clipboard_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_clipboard"]), self)
        self.clipboard_key.activated.connect(self.toggle_clipboard)


        self.delete_sentence_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["delete_sentence"]), self)
        self.delete_sentence_key.activated.connect(self.remove_sentence)



        self.zoom_in_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["zoom_in"]), self)
        self.zoom_in_key.activated.connect(self.zoom_minus)

        self.zoom_out_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["zoom_out"]), self)
        self.zoom_out_key.activated.connect(self.zoom_plus)

        self.zoom_in_numpad_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["zoom_in_numpad"]), self)
        self.zoom_in_numpad_key.activated.connect(self.zoom_plus)

        self.zoom_out_numpad_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["zoom_out_numpad"]), self)
        self.zoom_out_numpad_key.activated.connect(self.zoom_minus)

        self.show_main_window_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["show_main_window"]), self)
        self.show_main_window_shortcut.activated.connect(self.show_main_window)


        self.add_30 = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["add_30_seconds"]), self)
        self.add_30.activated.connect(self.add_30_seconds)

        self.add_60 = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["add_60_seconds"]), self)
        self.add_60.activated.connect(self.add_60_seconds)

        self.restart = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["restart_timer"]), self)
        self.restart.activated.connect(self.restart_timer)






    def closeEvent(self, event):
        """
        Handles cleanup when the window is closed.
        """
        view.display = None
        # Stop any active timers
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()

        # Disconnect any signals or shortcuts
        try:
            self.close


            # Add any other signal disconnections here
        except Exception as e:
            print(f"Error disconnecting signals: {e}")

        # Emit the closed signal
        self.closed.emit()

        # Call the parent class's closeEvent
        super(SessionDisplay, self).closeEvent(event)

        # Ensure the widget is deleted
        self.deleteLater()






    def apply_text_settings(self):
        font = QtGui.QFont()
        font.setPointSize(self.text_display_settings["font_size"])
        font.setFamily(self.text_display_settings.get("font_family", "Arial"))
        font.setWeight(self.text_display_settings.get("font_weight", QtGui.QFont.Normal))

        # Apply font to QLabel
        self.text_display.setFont(font)

        # Get RGB values for font color and background color
        color = self.text_display_settings.get("font_color", "black")



    def display_sentence(self, update_status=True):
        if not hasattr(self, 'session_info') or sip.isdeleted(self.session_info):
            return

        if self.playlist_position >= len(self.playlist):
            self.display_end_screen()
            return

        current_sentence = self.playlist[self.playlist_position]

        # Update session info (e.g., sentence counter)
        self.session_info.setText(f'{self.playlist_position + 1}/{len(self.playlist)}')

        # Apply text settings before displaying the sentence
        self.apply_text_settings()  # Call to apply text settings

        if self.highlight_toggle:
            # Display the sentence in the text_display with HTML formatting
            displayed_sentence = self.highlight_keywords(current_sentence)
        else:
            displayed_sentence = self.highlight_keywords(current_sentence, display=False)
        self.text_display.setText(displayed_sentence)

        if update_status:
            self.reset_timer()
        self.update_session_info()


    def highlight_keywords(self, sentence, display=True):
        """
        Highlights keywords with different font colors and weight:
        - Keywords between [| and |] are colored with self.highlight_names_color and bold weight.
        - Keywords between { and } are colored with self.highlight_keywords_color and bold weight.
        
        :param sentence: The sentence to process.
        :param display: If True, highlights keywords; if False, returns the sentence without highlights.
        """
        if not display:
            # Remove highlight brackets and return plain text
            sentence = re.sub(r'\[\|(.*?)\|\]', r'\1', sentence)  # Remove [|...|]
            sentence = re.sub(r'\{(.*?)\}', r'\1', sentence)       # Remove {...}
            return sentence

        # Replace [|...|] with self.highlight_names_color and bold weight
        sentence = re.sub(
            r'\[\|(.*?)\|\]', 
            rf'<span style="{self.highlight_names_settings}; ">\1</span>', 
            sentence
        )

        # Replace {...} with self.highlight_keywords_color and bold weight
        sentence = re.sub(
            r'\{(.*?)\}', 
            rf'<span style="{self.highlight_keywords_settings}">\1</span>', 
            sentence
        )

        return sentence

        

    def update_border_overlay_geometry(self, event=None):
        # Update the geometry to cover the entire window
        self.border_overlay.setGeometry(self.rect())

        # Optionally redraw the border if it is currently shown
        if self.border_overlay.isVisible():
            self.apply_border(True)


    def apply_border(self, show_border=True, border_width=1):
        border_color=self.always_on_top_borde_settings

        if show_border:
            self.border_overlay.show()
            self.border_overlay.raise_()  # Make sure it's above all other widgets

            # Create a pixmap for the border overlay that matches the window size
            border_pixmap = QtGui.QPixmap(self.size())
            border_pixmap.fill(QtCore.Qt.transparent)  # Transparent background

            # Parse the RGB color string into a QColor object
            if isinstance(border_color, str) and border_color.startswith("rgb"):
                # Extract the RGB values from the string
                rgb_values = [int(x) for x in border_color.replace("rgb(", "").replace(")", "").split(",")]
                q_color = QtGui.QColor(*rgb_values)
            else:
                # If it's already a QColor, use it directly
                q_color = QtGui.QColor(border_color)

            # Create a QPainter to draw the border
            painter = QtGui.QPainter(border_pixmap)
            pen = QtGui.QPen(q_color, border_width)
            painter.setPen(pen)

            # Draw the border as a rectangle around the edges
            # Use QRect adjusted to account for the pen width
            painter.drawRect(
                border_width // 2,
                border_width // 2,
                self.width() - border_width,
                self.height() - border_width
            )

            painter.end()

            # Set the pixmap to the border overlay label
            self.border_overlay.setPixmap(border_pixmap)
        else:
            self.border_overlay.hide()


    def toggle_highlight(self):
        if self.highlight_toggle is not True:
            # Toggle resize on
            self.highlight_toggle = True

            #self.toggle_highlight_button.setChecked(False)

            print("Highlight keyword: On")
        else:
            # Toggle resize off
            self.highlight_toggle = False

            #self.toggle_highlight_button.setChecked(True)


            print("Highlight keyword: Off")
        self.display_sentence()



    def zoom_plus(self):
        """
        Increases the size of the session_display window and the font size within limits.
        Limits the maximum size of the window and font size.
        """
        current_size = self.size()
        max_size = QtCore.QSize(1600, 1200)  # Set your desired maximum window size

        # Increase the size of the window
        new_width = current_size.width() + 100
        new_height = current_size.height() + 75

        # Ensure the window does not exceed the maximum size
        if new_width > max_size.width():
            new_width = max_size.width()
        if new_height > max_size.height():
            new_height = max_size.height()

        # Resize the window
        self.resize(new_width, new_height)

        # Increase the font size with limits
        max_font_size = 30  # Set your desired maximum font size
        current_font_size = self.text_display_settings["font_size"]
        new_font_size = current_font_size + 2  # Increase font size by 2

        if new_font_size > max_font_size:
            new_font_size = max_font_size  # Cap the font size at the maximum limit

        # Update text_display_settings
        self.text_display_settings["font_size"] = new_font_size  # Update the font size

        # Update the font size for self.lineEdit
        line_edit_font = self.lineEdit.font()  # Get current font
        line_edit_font.setPointSize(new_font_size)  # Set new font size
        self.lineEdit.setFont(line_edit_font)  # Apply the new font size

        # Update font size for QLineEdit
        line_edit_size = self.text_display_settings["font_size_lineedit"]
        new_line_edit_font_size = line_edit_size + 1  # Increase line edit font size by 1

        # Set a maximum font size for line edit if necessary
        max_line_edit_font_size = 16  # Example maximum size
        if new_line_edit_font_size > max_line_edit_font_size:
            new_line_edit_font_size = max_line_edit_font_size

        self.text_display_settings["font_size_lineedit"] = new_line_edit_font_size  # Update the font size for QLineEdit
        line_edit_font.setPointSize(new_line_edit_font_size)  # Update the font size for QLineEdit
        self.lineEdit.setFont(line_edit_font)  # Apply the new font size

        self.apply_text_settings()  # Apply the updated settings


    def zoom_minus(self):
        """
        Decreases the size of the session_display window and the font size within limits.
        Limits the minimum size of the window and font size.
        """
        current_size = self.size()
        min_size = QtCore.QSize(440, 200)  # Set your desired minimum window size

        # Decrease the size of the window
        new_width = current_size.width() - 100
        new_height = current_size.height() - 75

        # Ensure the window does not go below the minimum size
        if new_width < min_size.width():
            new_width = min_size.width()
        if new_height < min_size.height():
            new_height = min_size.height()

        # Resize the window
        self.resize(new_width, new_height)

        # Decrease the font size with limits
        min_font_size = 10  # Set your desired minimum font size
        current_font_size = self.text_display_settings["font_size"]
        new_font_size = current_font_size - 2  # Decrease font size by 2

        if new_font_size < min_font_size:
            new_font_size = min_font_size  # Cap the font size at the minimum limit

        # Update text_display_settings
        self.text_display_settings["font_size"] = new_font_size  # Update the font size

        # Update the font size for self.lineEdit
        line_edit_font = self.lineEdit.font()  # Get current font
        line_edit_font.setPointSize(new_font_size)  # Set new font size
        self.lineEdit.setFont(line_edit_font)  # Apply the new font size

        # Update font size for QLineEdit
        line_edit_font_size = self.text_display_settings["font_size_lineedit"]
        new_line_edit_font_size = line_edit_font_size - 1  # Decrease line edit font size by 1

        # Set a minimum font size for line edit if necessary
        if new_line_edit_font_size < 8:  # Example minimum size
            new_line_edit_font_size = 8

        self.text_display_settings["font_size_lineedit"] = new_line_edit_font_size  # Update the font size for QLineEdit
        line_edit_font.setPointSize(new_line_edit_font_size)  # Update the font size for QLineEdit
        self.lineEdit.setFont(line_edit_font)  # Apply the new font size

        self.apply_text_settings()  # Apply the updated settings





    def toggle_always_on_top(self):
        if not self.toggle_always_on_top_status:
            self.toggle_always_on_top_status = True
            self.setWindowFlag(
                QtCore.Qt.X11BypassWindowManagerHint,
                self.toggle_always_on_top_status
            )
            self.setWindowFlag(
                QtCore.Qt.WindowStaysOnTopHint,
                self.toggle_always_on_top_status
            )
            
            # Apply the border using the overlay
            self.apply_border(True)
            print('Always on top: On')
        else:
            self.toggle_always_on_top_status = False
            self.setWindowFlag(
                QtCore.Qt.WindowStaysOnTopHint,
                self.toggle_always_on_top_status
            )

            # Remove the border
            self.apply_border(False)
            print('Always on top: Off')
        
        self.show()

            ##################



    def load_entry(self):
        """
        Load the entry based on the current session settings.
        """
        # Check if the window is still valid
        if sip.isdeleted(self):
            print("SessionDisplay object has been deleted.")
            return

        if self.entry['current'] >= self.entry['total']:
            self.load_last_entry()
            return

        self.entry['time'] = int(self.schedule[self.entry['current']][2])
        self.timer.stop()
        self.time_seconds = self.entry['time']
        self.timer.start(500)
        self.entry['amount of items'] = int(self.schedule[self.entry['current']][1]) - 1
        if self.clipboard_settings == True:
            self.copy_sentence()
            self.clipboard_button.setChecked(True)




        self.display_sentence()

    def load_next_sentence(self):
        """
        Loads the next sentence in the playlist or displays an end screen if at the end.
        Resets the timer for a new sentence.
        """
 
        
        # Check if we are at the last sentence
        if self.playlist_position < len(self.playlist) - 1:
            self.playlist_position += 1  # Move to the next sentence
            self.new_entry = False
            self.reset_timer()  # Reset the timer for a new sentence
            self.display_sentence()  # Display the next sentence
        else:
            self.display_end_screen()  # Display end screen when at the end

        if self.clipboard_settings == True:
            self.copy_sentence()

        self.lineEdit.clear()
        self.lineEdit.setFocus() 
        self.update_session_info()

        # If there are any other buttons to untoggle, add them here



    def load_prev_sentence(self):
        """
        Loads the previous sentence in the playlist or does nothing if at the start.
        """

        # Check if we are at the first sentence
        if self.playlist_position > 0:
            self.playlist_position -= 1  # Move to the previous sentence
            self.new_entry = False
            self.display_sentence()  # Display the previous sentence
        else:
            return  # Do nothing if at the start of the playlist

        if self.clipboard_settings :
            self.copy_sentence()

        self.lineEdit.clear()
        self.lineEdit.setFocus() 
        self.update_session_info()


    def reset_timer(self):
        """
        Resets the timer to the initial time for the current sentence entry.
        """
        self.timer.stop()
        self.entry['time'] = int(self.schedule[self.entry['current']][2])  # Reset to the entry's time
        self.time_seconds = self.entry['time']
        self.timer.start(500)
        self.pause_timer.setChecked(False)
        self.timer_display.setFrameShape(QFrame.NoFrame)
        self.update_timer_display()

    def display_end_screen(self):
        """
        Display an end screen with a very small or transparent sentence and change the text to 'Done'.
        """
        # Create a transparent 1x1 pixel image
        transparent_pixmap = QtGui.QPixmap(1, 1)
        transparent_pixmap.fill(QtCore.Qt.transparent)

        # Set the image display to show the transparent image
        self.text_display.setPixmap(transparent_pixmap)

        # Stop the timer
        self.timer.stop()


        # Change the timer display text
        self.timer_display.setText('Done!')




    def toggle_text_field(self):
        if not self.text_toggle:
            # Toggle resize on
            self.text_toggle = True
            self.sizePolicy().setHeightForWidth(False)
            self.lineEdit.show()
            #self.toggle_text_button.setChecked(True)
            print("Toggle text field: On")
        else:
            # Toggle resize off
            self.text_toggle = False
            self.sizePolicy().setHeightForWidth(True)
            self.lineEdit.hide()
            #self.toggle_text_button.setChecked(False)
            print("Toggle text field: Off")




    def update_timer_display(self):
        """
        Update the timer display based on the remaining time.
        """
        hours = int(self.time_seconds / 3600)
        minutes = int((self.time_seconds % 3600) / 60)
        seconds = int(self.time_seconds % 60)

        self.hr_list = self.format_time_unit(hours)
        self.minutes_list = self.format_time_unit(minutes)
        self.sec = self.format_time_unit(seconds)

        self.display_time()


    def update_session_info(self):
        """
        Update the session info display based on the current sentence.
        """
        if hasattr(self, 'session_info') and not sip.isdeleted(self.session_info):
            self.session_info.setText(
                f'{self.playlist_position + 1}/{len(self.playlist)}'  # Update counter here
            )


        #############

    def update_entry_time(self):
        """Update the entry time and time_seconds."""
        self.entry['time'] = int(self.schedule[self.entry['current']][2])
        self.time_seconds = self.entry['time']

    def stop_timer(self):
        """Stop the timer."""
        self.timer.stop()

    def start_timer(self):
        """Start the timer."""
        self.timer.start(500)

    def countdown(self):
        """Countdown timer with sound alerts and sentence transitions."""
        # Check if the window is still valid
        if sip.isdeleted(self):
            self.timer.stop()
            return

        self.update_timer_display()

        if self.time_seconds == 0:
            QTest.qWait(500)
            self.load_next_sentence()
            return

        self.time_seconds -= 0.5




    def update_timer_display(self):
        """Update the timer display based on the remaining time."""
        hours = int(self.time_seconds / 3600)
        minutes = int((self.time_seconds % 3600) / 60)
        seconds = int(self.time_seconds % 60)

        self.hr_list = self.format_time_unit(hours)
        self.minutes_list = self.format_time_unit(minutes)
        self.sec = self.format_time_unit(seconds)

        self.display_time()

    def format_time_unit(self, value):
        """Format a time unit to be at least two digits."""
        return list(f"{value:02}")

    def pause(self):
        """Pause or resume the timer."""
        if self.timer.isActive():
            self.stop_timer()
            self.timer_display.setFrameShape(QFrame.WinPanel)
            self.pause_timer.setChecked(True)
            QTest.qWait(20)
        else:
            self.timer_display.setFrameShape(QFrame.NoFrame)
            self.pause_timer.setChecked(False)
            self.start_timer()

        self.display_time()


    def display_time(self):
        """Displays the amount of time left depending on how many seconds are left."""
        if not hasattr(self, 'timer_display') or self.timer_display is None:
            return  # Exit if timer_display doesn't exist or has been deleted

        # Ensure the QLabel has not been deleted
        if not sip.isdeleted(self.timer_display):
            if self.time_seconds >= 3600:
                # Hour or longer
                self.timer_display.setText(
                    f"{self.hr_list[0]}{self.hr_list[1]}:"
                    f"{self.minutes_list[0]}{self.minutes_list[1]}:"
                    f"{self.sec[0]}{self.sec[1]}"
                )
            elif self.time_seconds >= 60:
                # Minute or longer
                self.timer_display.setText(
                    f"{self.minutes_list[0]}{self.minutes_list[1]}:"
                    f"{self.sec[0]}{self.sec[1]}"
                )
            else:
                # Less than a minute left
                self.timer_display.setText(f"{self.sec[0]}{self.sec[1]}")


    def add_seconds(self, seconds):
        """Add seconds to the current timer."""
        self.time_seconds += seconds
        self.update_timer_display()

    def add_30_seconds(self):
        self.add_seconds(30)

    def add_60_seconds(self):
        self.add_seconds(60)

    def restart_timer(self):
        """Restart the timer with the current entry's time."""
        self.time_seconds = int(self.schedule[self.entry['current']][2])
        self.update_timer_display()

class GridSettingsDialog(QDialog):
    def __init__(self, parent=None,default_vertical = 4, default_horizontal = 4):
        super().__init__(parent)
        self.setWindowTitle("Grid Settings")

        # Remove the question mark from the title bar
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)

        # Layout for the dialog
        layout = QVBoxLayout()

        # Input fields for vertical and horizontal lines
        self.vertical_input = QSpinBox()
        self.vertical_input.setMinimum(1)
        self.vertical_input.setMaximum(20)
        self.vertical_input.setValue(default_vertical)  # Default value

        self.horizontal_input = QSpinBox()
        self.horizontal_input.setMinimum(1)
        self.horizontal_input.setMaximum(20)
        self.horizontal_input.setValue(default_horizontal)  # Default value

        # Labels
        layout.addWidget(QLabel("Vertical:"))
        layout.addWidget(self.vertical_input)
        layout.addWidget(QLabel("Horizontal:"))
        layout.addWidget(self.horizontal_input)

        # Create OK and Cancel buttons
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")


        # Connect buttons
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        # Add buttons to a horizontal layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        # Add button layout to the main layout
        layout.addLayout(button_layout)

        self.setLayout(layout)
    def get_values(self):
        return self.vertical_input.value(), self.horizontal_input.value()


class MaxLengthDelegate(QStyledItemDelegate):
    def __init__(self, max_length=60, parent=None):
        super().__init__(parent)
        self.max_length = max_length

    def createEditor(self, parent, option, index):
        # Create a QLineEdit editor
        editor = QLineEdit(parent)
        # Set the maximum length of characters allowed
        editor.setMaxLength(self.max_length)
        return editor

            # Subclass to enable multifolder selection.


class MultiFolderSelector(QtWidgets.QDialog):
    def __init__(self, parent=None, preset_name="preset_1", stylesheet=""):
        super(MultiFolderSelector, self).__init__(parent)
        self.setWindowTitle("Select Folders")

        self.setMinimumWidth(400)
        self.setMinimumHeight(500)  # Adjusted height to accommodate the new input fields

        # Remove the question mark button by setting the window flags
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        # Initialize selected folders list
        self.selected_folders = []
        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # List widget to display selected folders
        self.list_widget = QtWidgets.QListWidget(self)
        layout.addWidget(self.list_widget)

        # Preset Name Input (below the list widget)
        self.preset_name_edit = QtWidgets.QLineEdit(self)
        self.preset_name_edit.setPlaceholderText("Enter Preset Name")
        self.preset_name_edit.setText(preset_name)
        layout.addWidget(self.preset_name_edit)

        # Scrollable text input for keywords
        self.keyword_input = QtWidgets.QTextEdit(self)
        self.keyword_input.setPlaceholderText(
            "Enter keywords (one per line)\n\n"
            "\"Keyword\" : search for both singular and plural forms\n"
            "\"&Keyword\" : search the given form\n\n"
            "\"!Keyword\" : ignore sentences with either singular or plural forms\n"
            "\"!&Keyword\" : ignore sentences with the given form\n\n"
            "\"#Name\" : highlight name\n"
            "\"@Name\" : search and highlight name\n\n"

            "\";Comment\" : ignore line "
        )
        self.keyword_input.setMinimumHeight(100)  # Set a minimum height for the text input
        layout.addWidget(self.keyword_input)

        self.keyword_input.setPlainText("")

        # Checkbox for "Highlight Keywords"
        self.highlight_keywords_checkbox = QtWidgets.QCheckBox("Highlight Keywords", self)
        self.highlight_keywords_checkbox.setChecked(True)  # Check the checkbox by default
        layout.addWidget(self.highlight_keywords_checkbox)

        # Dropdown menu for output options
        self.output_option_dropdown = QtWidgets.QComboBox(self)
        self.output_option_dropdown.addItems(["Single output", "All output"])
        layout.addWidget(self.output_option_dropdown)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        # Button for adding folders
        self.add_folders_button = QtWidgets.QPushButton("Add Folder(s)", self)
        self.add_folders_button.clicked.connect(self.multi_select_folders)
        self.add_folders_button.setAutoDefault(False)
        button_layout.addWidget(self.add_folders_button)

        # Button to remove selected folder
        self.remove_button = QtWidgets.QPushButton("Remove folder", self)
        self.remove_button.clicked.connect(self.remove_folder)
        self.remove_button.setAutoDefault(False)
        button_layout.addWidget(self.remove_button)

        # OK and Cancel buttons
        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setAutoDefault(True)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setAutoDefault(False)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Apply passed stylesheet
        self.setStyleSheet(stylesheet)

        # Set the default focus to the list widget
        self.list_widget.setFocus()

        # Ensure Enter triggers OK button
        self.ok_button.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.init_message_boxes()

    def get_highlight_keywords_option(self):
        """Returns whether the 'Highlight Keywords' checkbox is checked."""
        return self.highlight_keywords_checkbox.isChecked()

    def get_output_option(self):
        """Returns the selected output option from the dropdown menu."""
        return self.output_option_dropdown.currentText()

    def get_selected_folders(self):
        """Return the selected folders."""
        return self.selected_folders

    def get_keyword_input(self):
        """Return the keywords entered by the user as a list, separated by line breaks."""
        keywords = self.keyword_input.toPlainText().splitlines()
        return [kw.strip() for kw in keywords if kw.strip()]  # Return only non-empty lines

    def get_preset_name(self):
        """Return the preset name entered by the user."""
        return self.preset_name_edit.text()

        
    def init_message_boxes(self):
        """Initialize custom message box settings."""
        self.message_box = QtWidgets.QMessageBox(self)
        self.message_box.setIcon(QtWidgets.QMessageBox.NoIcon)  # Set to no icon by default
    
    def show_info_message(self, title, message):
        """Show an information message box without an icon."""
        self.message_box.setWindowTitle(title)
        self.message_box.setText(message)
        self.message_box.exec_()


    def format_folder_path(self, folder_path):
        """Format the folder path to display only the end part."""
        # Normalize the path to use backslashes
        normalized_path = folder_path.replace('/', os.sep).replace('\\', os.sep)

        # Split the normalized path into parts
        parts = normalized_path.split(os.sep)

        # Debug print
        print("Normalized Path:", normalized_path)
        print("Path Parts:", parts)

        # If there are more than 2 parts, keep the last two parts
        if len(parts) > 3:
            return '...\\' + os.sep.join(parts[-3:])  # Show the last two parts of the path
        return normalized_path  # If less than or equal, return as is


        
    def multi_select_folders(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_dialog.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        file_view = file_dialog.findChild(QListView, 'listView')
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)

        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        # Variable to store the last navigated directory
        last_directory = None

        def update_last_directory(directory):
            nonlocal last_directory
            last_directory = directory

        file_dialog.directoryEntered.connect(update_last_directory)

        if file_dialog.exec():
            folders = file_dialog.selectedFiles()

            # Filter out the parent directory if included mistakenly
            filtered_folders = [
                folder for folder in folders if folder != last_directory
            ]

            # Add the filtered folders to the selected list
            for folder in filtered_folders:
                if folder and folder not in self.selected_folders:
                    self.selected_folders.append(folder)
                    formatted_path = self.format_folder_path(folder)
                    self.list_widget.addItem(formatted_path)

    def remove_folder(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                # Find the full path corresponding to the formatted path in the list
                formatted_path = item.text()
                full_path = None

                # Iterate through the selected_folders to find the matching full path
                for folder in self.selected_folders:
                    if self.format_folder_path(folder) == formatted_path:
                        full_path = folder
                        break

                # If full path is found, remove it
                if full_path:
                    self.selected_folders.remove(full_path)

                # Remove the item from the list widget
                self.list_widget.takeItem(self.list_widget.row(item))

    def get_selected_folders(self):
        return self.selected_folders

    def get_preset_name(self):
        return self.preset_name_edit.text()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # Trigger OK button click
            self.ok_button.click()
        else:
            super(MultiFolderSelector, self).keyPressEvent(event)

    def accept(self):
        """Accept the dialog and check for existing presets before processing."""
        preset_name = self.get_preset_name().strip()

        # Check if the preset name already exists
        text_presets_dir = self.parent().text_presets_dir  # Assume parent has this attribute
        preset_filename = f'{preset_name}.txt'
        preset_filepath = os.path.join(text_presets_dir, preset_filename)

        if os.path.exists(preset_filepath):
            self.show_info_message( 'Duplicate Preset', f'The preset "{preset_name}" already exists. Please choose a different name.')
            return  # Do not accept the dialog

        super(MultiFolderSelector, self).accept()


class ThemeSelectorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, theme_presets_dir="", session_settings_file=""):
        super(ThemeSelectorDialog, self).__init__(parent)
        self.setWindowTitle("Select Theme")
        self.setMinimumWidth(300)  
        self.setMinimumHeight(100)  

        self.setMaximumWidth(300)  
        self.setMaximumHeight(150)  
        # Remove the question mark button by setting the window flags
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.theme_presets_dir = theme_presets_dir
        self.current_theme = self.load_current_theme(session_settings_file)

        # Initialize selected theme
        self.selected_theme = None

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # List widget to display theme files
        self.list_widget = QtWidgets.QListWidget(self)
        layout.addWidget(self.list_widget)

        # Populate list with theme files
        self.load_theme_files()

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setAutoDefault(True)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setAutoDefault(False)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set the default focus to the list widget
        self.list_widget.setFocus()  # Set focus to the list widget

        # Ensure Enter triggers OK button
        self.ok_button.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Connect double click to select theme
        self.list_widget.itemDoubleClicked.connect(self.accept)

    def load_current_theme(self, session_settings_file):
        """Load the current theme from the session settings file."""
        if not os.path.exists(session_settings_file):
            return ""  # Default if settings file does not exist

        with open(session_settings_file, 'r') as file:
            settings = json.load(file)
        
        return settings.get("theme_settings", "").replace('.txt', '')

    def load_theme_files(self):
        """Load theme files from the theme presets directory and set the current theme as selected."""
        theme_files = [f for f in os.listdir(self.theme_presets_dir) if f.endswith('.txt')]

        # Separate the default theme, if it exists
        default_theme = "default_theme.txt"
        other_themes = [f for f in theme_files if f != default_theme]

        # Sort the other themes alphabetically
        sorted_themes = sorted([f.replace('.txt', '') for f in other_themes])

        # Add the default theme at the top
        if default_theme in theme_files:
            sorted_themes.insert(0, default_theme.replace('.txt', ''))

        # Add themes to the list widget
        for theme_name in sorted_themes:
            item = QtWidgets.QListWidgetItem(theme_name)
            if theme_name == self.current_theme:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)  # Update the current item to reflect the selection
            self.list_widget.addItem(item)

    def accept(self):
        """Accept the dialog and set the selected theme."""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_theme = selected_items[0].text() + ".txt" # Add back the .txt extension

        super(ThemeSelectorDialog, self).accept()

    def get_selected_theme(self):
        """Get the selected theme."""
        return self.selected_theme 

if __name__ == "__main__":
    import sys
    show_main_window = True  # Set to True to show the main window
    app = QtWidgets.QApplication(sys.argv)
    view = MainApp(show_main_window=show_main_window)
    sys.exit(app.exec_())




    
