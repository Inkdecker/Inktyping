# OS 
import os
import sys
import argparse
import subprocess
import random
import shutil
import json  
import datetime  

from send2trash import send2trash
from pathlib import Path

# Text stuff
import re
import inflect
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import PyPDF2
import time
from html import escape


# PyQT 
from PyQt5 import QtGui
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QEvent, QItemSelectionModel
from PyQt5.QtGui import QFont, QColor
from PyQt5 import QtCore, QtWidgets
import sip


# App 
from main_window import Ui_MainWindow
from session_display import Ui_session_display
import resources_config_rc  




class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, show_main_window=False):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Reference Practice')
        self.session_schedule = {}
        # Install event filter
        self.installEventFilter(self)
        
        self.plural = inflect.engine()



        # Disable tab focus for all widgets
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.setFocusPolicy(QtCore.Qt.ClickFocus)
        
        # Initialize label dictionaries
        self.labels_color_dictionary = {"Default": "#00000000"}
        self.preset_labels_dictionary = {}


        # Define default shortcuts
        self.default_shortcuts = {
            "main_window": {
                "start": "S", 
                "close": "Escape",
                "cycle_label": "\u00b2"
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


        # Load session settings at startup
        self.load_session_settings()
        self.init_buttons()
        self.apply_shortcuts_main_window()
        self.table_sentences_selection.setItem(0, 0, QTableWidgetItem('112'))

        # Enable sorting on table headers
        self.table_sentences_selection.setSortingEnabled(True)
        self.table_session_selection.setSortingEnabled(True)


        # Alternative method (ensures interactivity)
        self.table_sentences_selection.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table_session_selection.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)


  


        
        self.load_session_settings()

        self.schedule = []
        self.total_time = 0
        self.selection = {'folders': [], 'files': []}

        self.KEYWORDS_TYPES = {}




        # Hide the main window initially
        #self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)

        self.display = None  # Initialize with None

        # Automatically start the session if auto_start is True
        if self.auto_start_settings:
            self.start_session_from_files()

        # Show the main window if show_main_window is True
        elif show_main_window == True:
            self.show()

        # Initialize position for dragging
        self.oldPos = self.pos()
        self.init_styles()
        self.load_presets()
    


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
        self.start_session_button.clicked.connect(self.start_session_launcher)
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
        #self.table_sentences_selection.itemChanged.connect(self.rename_presets)
        #self.table_session_selection.itemChanged.connect(self.rename_presets)





        self.table_sentences_selection.itemChanged.connect(self.handle_preset_rename)
        self.table_session_selection.itemChanged.connect(self.handle_preset_rename)
        
        # Track editing state to prevent duplicate signals
        self.currently_editing = False
        self.current_edited_item = None
        
        # Connect itemDoubleClicked to start tracking edits
        self.table_sentences_selection.itemDoubleClicked.connect(self.start_edit_tracking)
        self.table_session_selection.itemDoubleClicked.connect(self.start_edit_tracking)
        
        # Install event filters to catch Return/Enter key
        self.table_sentences_selection.installEventFilter(self)
        self.table_session_selection.installEventFilter(self)

        # Assuming these are your QTableWidget instances
        self.table_sentences_selection.selectionModel().selectionChanged.connect(self.update_selection_cache)
        self.table_session_selection.selectionModel().selectionChanged.connect(self.update_selection_cache)


        # Theme selector button
        self.theme_options_button.clicked.connect(self.open_theme_selector)

        # Preset search
        self.search_preset.textChanged.connect(self.filter_presets)



        # Connect label options button
        self.labels_options_button.clicked.connect(self.open_label_manager)
        
        # Add context menu to table_sentences_selection
        self.table_sentences_selection.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_sentences_selection.customContextMenuRequested.connect(self.show_sentence_context_menu)






    def show_sentence_context_menu(self, position):
        """Show context menu for the sentence table with direct label assignment options."""
        selected_row = self.table_sentences_selection.currentRow()
        if selected_row < 0:
            return
            
        file_item = self.table_sentences_selection.item(selected_row, 1)  # Name column
        if not file_item:
            return
            
        filename = file_item.text() + ".txt"
        
        context_menu = QMenu(self)
        
        # Add label options directly to the context menu
        for label_name, color in sorted(self.labels_color_dictionary.items()):
            action = context_menu.addAction(label_name)
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QColor(color))
            action.setIcon(QtGui.QIcon(pixmap))
            
            # Check the current label
            current_label = self.preset_labels_dictionary.get(filename, "Default")
            if label_name == current_label:
                action.setCheckable(True)
                action.setChecked(True)
                
            # Connect the action
            action.triggered.connect(lambda checked, ln=label_name: self.assign_label(filename, ln))
        
        # Show the menu
        context_menu.exec_(self.table_sentences_selection.viewport().mapToGlobal(position))


    def assign_label(self, filename, label_name):
        """Assign a label to a preset file."""
        self.preset_labels_dictionary[filename] = label_name
        self.save_session_settings()
        
        # Update the UI
        selected_row = self.table_sentences_selection.currentRow()
        if selected_row >= 0:
            color_item = self.table_sentences_selection.item(selected_row, 0)
            if color_item:
                color = self.labels_color_dictionary.get(label_name, "#00000000")
                color_item.setBackground(QColor(color))
                color_item.setToolTip(label_name)



    def start_edit_tracking(self, item):
        """Called when double-clicking to edit an item"""
        self.currently_editing = True
        self.current_edited_item = item
        self.original_text = item.text()  # Store original value

    def eventFilter(self, source, event):
        """Handle Return/Enter key press during editing"""
        if (event.type() == QtCore.QEvent.KeyPress and
            event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) and
            source.state() == QtWidgets.QAbstractItemView.EditingState):
            
            # Force close the editor
            source.closePersistentEditor(source.currentItem())
            return True  # Event handled
        
        return super().eventFilter(source, event)

    def handle_preset_rename(self, item):
        """Handle the actual renaming after edit completes"""
        if not self.currently_editing or item != self.current_edited_item:
            return
        
        # Store these values before potentially modifying state
        was_editing = self.currently_editing
        original_text = self.original_text
        
        # Reset editing state BEFORE making changes
        self.currently_editing = False
        self.current_edited_item = None
        
        # Only proceed if text actually changed
        if item.text() != original_text:
            if self.sender() == self.table_sentences_selection or self.sender() == self.table_session_selection:
                # Pass success/failure back from rename_presets
                success = self.rename_presets(item)
                if not success:
                    # Set the text back to original without triggering events
                    self.blockSignals(True)
                    item.setText(original_text)
                    self.blockSignals(False)


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
                            style_sheet_header = ""
                            for selector, style in element_styles.items():
                                
                                if selector == "QHeaderView::section":
                                    style_sheet_header += f"{selector} {{{style}}}\n"
                                else:

                                    style_sheet += f"{selector} {{{style}}}\n"
                            dialog.setStyleSheet(style_sheet)
                            if isinstance(dialog, LabelManagerDialog):
                                dialog.label_list.horizontalHeader().setStyleSheet(style_sheet_header)

                        elif "dictionary_controls" in styles_dict and dialog and isinstance(dialog, MultiFolderSelector):
                            style_dict = styles_dict["dictionary_controls"]
                            
                            # Apply styles to checkboxes
                            if "checkbox" in style_dict:
                                style_sheet = ""
                                for selector, style in style_dict["checkbox"].items():
                                    style_sheet += f"{selector} {{{style}}}\n"
                                
                                for i in range(10):  # 0-9 (including the ignored keywords)
                                    checkbox = dialog.findChild(QtWidgets.QCheckBox, f"dictionary_checkbox_{i}")
                                    if checkbox:
                                        checkbox.setStyleSheet(style_sheet)
                            


                            # Apply styles to labels
                            if "label" in style_dict:
                                style_sheet = ""
                                for selector, style in style_dict["label"].items():
                                    style_sheet += f"{selector} {{{style}}}\n"
                                
                                for i in range(10):
                                    label = dialog.findChild(QtWidgets.QLabel, f"dictionary_label_{i}")
                                    if label:
                                        label.setStyleSheet(style_sheet)
                            
                            # Apply styles to path edits
                            if "path_edit" in style_dict:
                                style_sheet = ""
                                for selector, style in style_dict["path_edit"].items():
                                    style_sheet += f"{selector} {{{style}}}\n"
                                
                                for i in range(10):
                                    path_edit = dialog.findChild(QtWidgets.QLineEdit, f"dictionary_path_edit_{i}")
                                    if path_edit:
                                        path_edit.setStyleSheet(style_sheet)
                            
                            # Apply styles to browse buttons
                            if "browse_button" in style_dict:
                                style_sheet = ""
                                for selector, style in style_dict["browse_button"].items():
                                    style_sheet += f"{selector} {{{style}}}\n"
                                
                                for i in range(10):
                                    browse_button = dialog.findChild(QtWidgets.QPushButton, f"dictionary_browse_button_{i}")
                                    if browse_button:
                                        browse_button.setStyleSheet(style_sheet)

                            if "dictionary_container" in styles_dict and dialog and isinstance(dialog, MultiFolderSelector):
                                style_sheet = ""
                                for selector, style in styles_dict["dictionary_container"].items():
                                    style_sheet += f"{selector} {{{style}}}\n"
                                dialog.dictionary_container.setStyleSheet(style_sheet)
                                
                                # And for the content widget
                                if hasattr(dialog, 'dictionary_content'):
                                    dialog.dictionary_content.setStyleSheet(style_sheet)


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
                    for button_name in ["theme_options_button","labels_options_button", "add_folders_button", "delete_sentences_preset", "open_preset_button","rainmeter_preset_button",
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
        


    def update_selection_cache(self):
        """Update the selected filename cache based on current table selections."""
        # Only proceed if signals aren't blocked
        if not self.table_sentences_selection.signalsBlocked() and not self.table_session_selection.signalsBlocked():
            print("-- updating cache --")
            # Track sentence selection by filename
            selected_row = self.table_sentences_selection.currentRow()
            if selected_row >= 0:
                name_item = self.table_sentences_selection.item(selected_row, 1)  # Name column
                if name_item:
                    # Store both filename and row number
                    self.selected_sentence_filename = name_item.text() + ".txt"
                    self.selected_sentence_row = selected_row

            # Track session selection by filename
            selected_row = self.table_session_selection.currentRow()
            if selected_row >= 0:
                name_item = self.table_session_selection.item(selected_row, 0)  # Name column
                if name_item:
                    # Store both filename and row number
                    self.selected_session_filename = name_item.text() + ".txt"
                    self.selected_session_row = selected_row

    def filter_presets(self):
        """Filter table_sentences_selection based on search_preset input."""
        search_text = self.search_preset.text().strip().lower()
        
        for row in range(self.table_sentences_selection.rowCount()):
            item = self.table_sentences_selection.item(row, 1)  # Assuming filenames are in column 0
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

    
########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################

    def create_preset(self, selected_files=None, keyword_profiles=None, preset_name=None, highlight_keywords=True, 
                      output_option="Single output", max_length=200, metadata_settings=True, output_folder=None, is_gui=True, metadata_prefix=";;"):
        """
        Opens a dialog for folder selection, collects keyword profiles, and processes all EPUB, PDF, and TXT files 
        within the selected folders using the chosen profiles. Combines results from all folders.
        """
        # Start timer
        self.load_presets()


        if is_gui:

            dialog = MultiFolderSelector(self, preset_name, text_presets_dir=self.text_presets_dir)

            self.init_styles(dialog=dialog)

            for child in dialog.findChildren(QtWidgets.QWidget):
                child.style().unpolish(child)
                child.style().polish(child)

            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                selected_files = dialog.selected_files
                highlight_keywords = dialog.highlight_keywords_checkbox.isChecked()
                output_option = dialog.output_option_dropdown.currentText()
                metadata_settings = dialog.extract_metadata_checkbox.isChecked()
                if preset_name == None:
                    preset_name = dialog.preset_name_edit.text()

                max_length = int(dialog.max_length_edit.text()) if dialog.max_length_edit.text().isdigit() else 200
                keyword_profiles = dialog.get_all_keyword_profiles()
                

                #print("keyword_profiles : ", keyword_profiles)
                if not selected_files:
                    self.show_info_message('No Selection', 'No files were selected.')
                    return
            else:
                return

        # Ensure we have directories to process
        if not selected_files:
            if is_gui:
                self.show_info_message('No Selection', 'No folders were selected.')
            return

        # Dictionary to store all results
        all_results = {}
        total_sentences = 0  # Counter for total unique sentences



        # Start timer    
        start_time = time.time()




        folder_results = self.process_text_files(
                file_paths=selected_files,
                keyword_profiles=keyword_profiles,
                highlight_keywords=highlight_keywords,
                output_option=output_option,
                preset_name=preset_name,
                max_length=max_length,
                metadata_settings=metadata_settings
            )




        # Merge results
        for keyword, sentences in folder_results.items():
            if keyword not in all_results:
                all_results[keyword] = []
            all_results[keyword].extend(sentences)

        # Determine the output folder
        target_folder = output_folder if output_folder else self.text_presets_dir
        os.makedirs(target_folder, exist_ok=True)

        # Create the combined output file and count unique sentences
        combined_output_path = os.path.join(target_folder, f"{preset_name}.txt")
        seen_sentences = set()

        with open(combined_output_path, 'w', encoding='utf-8') as output_file:
            for sentences in all_results.values():
                for sentence_data in sentences:
                    sentence_key = (sentence_data[0], sentence_data[1])  # sentence and filepath
                    if sentence_key not in seen_sentences:
                        seen_sentences.add(sentence_key)
                        total_sentences += 1
                        if metadata_settings:
                            sentence, filepath, metadata = sentence_data  # Now includes metadata
                            output_file.write(f'["""{sentence}""","""{metadata}"""]\n\n')
                        else:
                            sentence = sentence_data[0]
                            output_file.write(f'{sentence}\n\n')

        # If "All output" is selected, create individual keyword files
        if output_option == "All output":
            for keyword, sentences in all_results.items():
                if sentences:
                    keyword_output_path = os.path.join(
                        target_folder, f"{preset_name}_{keyword}.txt"
                    )
                    with open(keyword_output_path, 'w', encoding='utf-8') as output_file:
                        for sentence_data in sentences:
                            if metadata_settings:
                                sentence, filepath, metadata = sentence_data
                                output_file.write(f'["""{sentence}""","""{metadata}"""]\n\n')
                            else:
                                sentence = sentence_data[0]
                                output_file.write(f'{sentence}\n\n')

        # End timer and calculate elapsed time
        elapsed_time = time.time() - start_time

        # Show summary message and reload presets if using GUI
        summary_message = (f"Successfully extracted {total_sentences} unique sentences to: {preset_name}.txt in {elapsed_time:.2f} seconds!")
        if is_gui:
            self.show_info_message('Extraction Complete', summary_message)
            self.load_presets()
        print(summary_message)









    def create_keyword_profiles(self, keyword_input):
        """
        Creates keyword profiles based on the user input.
        """
        profiles = []
        for kw in keyword_input:
            if not kw.startswith(';'):  # Ignore comments (those starting with ;)
                profile = self.create_single_keyword_profile(kw)  # Use a method to create a single keyword profile
                profiles.append(profile)
        return profiles

    def create_single_keyword_profile(self, keyword):
        """
        Creates a single keyword profile.
        Modify this method based on how you want each keyword profile to be structured.
        """
        # Example of simple profile creation
        return {'keyword': keyword, 'options': {'highlight': True}}  # Customize as necessary








    def process_text_files(self, file_paths, keyword_profiles, highlight_keywords=True, output_option="Single output", preset_name="preset_output", max_length=200, metadata_settings=True, metadata_prefix=";;"):
        """
        Process a folder of EPUB, PDF, or text files and return the extracted sentences.
        Returns a tuple of (filtered_sentences, folder_path) where filtered_sentences is a dictionary
        of keyword-sentence pairs with their complete file paths.
        """
        
        # Process ignored keywords
        ignored_keywords = keyword_profiles.get("Ignored keywords", [])
        # Remove "Ignored keywords" from profiles for processing
        if "Ignored keywords" in keyword_profiles:
            del keyword_profiles["Ignored keywords"]

        # Remove duplicates across all profiles
        seen_keywords = set()
        for profile, keywords in keyword_profiles.items():
            unique_keywords = []
            for keyword in keywords:
                if keyword not in seen_keywords:
                    unique_keywords.append(keyword)
                    seen_keywords.add(keyword)
            keyword_profiles[profile] = unique_keywords

        # Remove duplicates from ignored keywords
        ignored_keywords = list(set(ignored_keywords))

        #print("Keywords by profile (unique)[0:5]:", keyword_profiles)
        #print("Ignored keywords (unique)[0:5]:", ignored_keywords)

        # Gather all files in the specified folder


        # Initialize storage for combined sentences and processed keywords
        combined_sentences = {
            keyword: [] for keywords in keyword_profiles.values() 
            for keyword in keywords
        }
        processed_keywords = []

        # Process all profiles and extract sentences
        for profile_number, keywords in keyword_profiles.items():
            if keywords:
                self.extract_sentences_with_keywords(
                    file_paths, keywords, combined_sentences, 
                    processed_keywords, max_length, metadata_settings, metadata_prefix
                )

        # Filter out sentences with ignored keywords and store full file paths
        filtered_sentences = {
            keyword: [
                sentence_data for sentence_data in sentences
                if not self.contains_ignored_keyword(sentence_data[0], ignored_keywords)
            ]
            for keyword, sentences in combined_sentences.items()
        }

        # Reset processed keywords for highlighting
        processed_keywords = []

        # Highlight keywords if requested
        if highlight_keywords:
            filtered_sentences = self.process_highlight_keywords(
                filtered_sentences, keyword_profiles, processed_keywords
            )

        return filtered_sentences

    def get_book_metadata(self, file_path, metadata_prefix=";;"):
        """
        Extract metadata from book files.
        Returns metadata string with optional prefix from filename.
        """
        filename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Extract prefix if present
        prefix = ""
        if metadata_prefix in filename_without_ext:
            prefix, rest = filename_without_ext.split(metadata_prefix, 1)
            filename_without_ext = rest.replace('_', ' ').strip()
        
        # Default values
        title = filename_without_ext
        author = "Unknown Author"
        date = "Unknown Date"
        
        try:
            if file_path.endswith('.epub'):
                book = epub.read_epub(file_path)
                
                # Get title
                if book.get_metadata('DC', 'title'):
                    title = book.get_metadata('DC', 'title')[0][0]
                
                # Get author
                if book.get_metadata('DC', 'creator'):
                    author = book.get_metadata('DC', 'creator')[0][0]
                
                # Get date
                if book.get_metadata('DC', 'date'):
                    date = book.get_metadata('DC', 'date')[0][0]
                    year_match = re.search(r'\d{4}', date)
                    if year_match:
                        date = year_match.group(0)
                
            elif file_path.endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.metadata:
                        if reader.metadata.get('/Title'):
                            title = reader.metadata['/Title']
                        if reader.metadata.get('/Author'):
                            author = reader.metadata['/Author']
                        if reader.metadata.get('/CreationDate'):
                            date_str = reader.metadata['/CreationDate']
                            year_match = re.search(r'D:(\d{4})', date_str)
                            if year_match:
                                date = year_match.group(1)
            
            # Clean up metadata
            title = title.strip()
            author = author.strip()
            date = date.strip()
            
            if not title:
                title = filename_without_ext
                
        except Exception as e:
            print(f"Error extracting metadata from {filename}: {str(e)}")
            title = filename_without_ext
        
        # Format the metadata string with prefix
        metadata = prefix.strip()
        if metadata:
            metadata += " - "
        metadata += title
        if author != "Unknown Author":
            metadata += f" by {author}"
        if date != "Unknown Date":
            metadata += f" - {date}"
        
        return metadata



    def get_keyword_forms(self, keyword):
        """
        Get the forms of a keyword, handling the '&' prefix and combined keywords.
        Returns a list of forms and a boolean indicating if it's an exact match.
        """
        if '+' in keyword:
            # Split combined keywords and process each part
            parts = [k.strip() for k in keyword.split('+')]
            all_forms = []
            exact_matches = []
            
            for part in parts:
                if part.startswith('&'):
                    all_forms.append([part[1:]])  # Exact form only
                    exact_matches.append(True)
                else:
                    all_forms.append([self.get_singular_form(part), self.get_plural_form(part)])
                    exact_matches.append(False)
            
            return all_forms, exact_matches
        else:
            if keyword.startswith('&'):
                return [[keyword[1:]]], [True]  # Single keyword, exact match
            else:
                return [[self.get_singular_form(keyword), self.get_plural_form(keyword)]], [False]  # Single keyword, both forms



    def contains_ignored_keyword(self, sentence, ignored_keywords):
        """
        Check if a sentence contains any of the ignored keywords.
        Handles both regular ignored keywords and exact matches (with & prefix).
        """
        for ignored_keyword in ignored_keywords:
            # Remove the ! prefix first
            keyword = ignored_keyword.lstrip('!')
            
            # Get the forms to check (handles both exact and regular matches)
            forms_to_check, exact_matches = self.get_keyword_forms(keyword)
            
            # Check each form
            for form_group, is_exact in zip(forms_to_check, exact_matches):
                for form in form_group:
                    # For exact matches (with &), we need to match the exact form
                    if is_exact:
                        pattern = r'(?<!\w){}(?!\w)'.format(re.escape(form))
                    else:
                        pattern = r'\b{}\b'.format(re.escape(form))
                    
                    if re.search(pattern, sentence, re.IGNORECASE):
                        return True
        return False   




    def process_highlight_keywords(self, filtered_sentences, profiles, processed_keywords):
        """
        Highlight keywords and their forms in sentences with the appropriate number of brackets based on the profile name.
        Updated to handle metadata in sentence data.
        """
        for profile_name, keywords in profiles.items():
            # Extract the numeric part from the profile name (e.g., 'Keywords_1' -> 1)
            match = re.search(r'(\d+)', profile_name)
            bracket_count = int(match.group(1)) if match else 1  # Default to 1 if no number is found

            # Construct the bracket style for this profile
            left_bracket = "{" * bracket_count
            right_bracket = "}" * bracket_count

            # Process each keyword in the profile
            for keyword in keywords:
                # Get all forms of the keyword(s)
                forms_list, exact_matches = self.get_keyword_forms(keyword)
                
                # Flatten the forms list for highlighting
                all_forms = [form for sublist in forms_list for form in sublist]
                forms_lower = [form.lower() for form in all_forms]
                
                if any(form in processed_keywords for form in forms_lower):
                    continue
                
                # Create pattern to match any of the keyword forms
                pattern = re.compile(
                    r'(?<!\w)({})\b'.format("|".join(map(re.escape, all_forms))), 
                    re.IGNORECASE
                )

                # Highlight keywords in all sentences
                for key, sentence_data_list in filtered_sentences.items():
                    for i, sentence_data in enumerate(sentence_data_list):
                        def replace_func(match):
                            # Wrap the matched word in the appropriate brackets
                            original_word = match.group(0)
                            return f"{left_bracket}{original_word}{right_bracket}"

                        # Update the sentence with highlighted keywords, preserving the metadata
                        if len(sentence_data) == 3:  # If we have metadata
                            sentence, filepath, metadata = sentence_data
                            highlighted_sentence = pattern.sub(replace_func, sentence)
                            filtered_sentences[key][i] = (highlighted_sentence, filepath, metadata)
                        else:  # If we don't have metadata
                            sentence, filepath = sentence_data
                            highlighted_sentence = pattern.sub(replace_func, sentence)
                            filtered_sentences[key][i] = (highlighted_sentence, filepath)

                # Add all forms to processed_keywords
                for form in all_forms:
                    processed_keywords.append(form.lower())

        return filtered_sentences



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
        return self.plural.plural(keyword)

    def get_singular_form(self, keyword):
        # For words already in singular form
        if self.plural.singular_noun(keyword) == False:
            return keyword
        # For plurals
        return self.plural.singular_noun(keyword)

                
    def extract_sentences_with_keywords(self, file_paths, keywords, combined_sentences, processed_keywords, max_length, metadata_settings=True, metadata_prefix=";;"):
        """
        Extract sentences containing the provided keywords from the list of files.
        Optimized to process each file only once and pre-filter keywords.
        """
        def match_keywords(forms_list, exact_matches, sentence, max_length=200):
            def find_keyword_in_sentence(forms, exact_match, sentence):
                for form in forms:
                    if re.search(r'\b{}\b'.format(re.escape(form)), sentence, re.IGNORECASE):
                        return form
                return None

            found_keywords = []
            for forms, exact_match in zip(forms_list, exact_matches):
                found_keyword = find_keyword_in_sentence(forms, exact_match, sentence)
                if not found_keyword:
                    return False
                found_keywords.append(found_keyword)

            return truncate_sentence_around_keywords(sentence, found_keywords, max_length)

        def truncate_sentence_around_keywords(sentence, keywords, max_length=200):
            positions = []
            for keyword in keywords:
                match = re.search(r'\b{}\b'.format(re.escape(keyword)), sentence, re.IGNORECASE)
                if match:
                    positions.append((match.start(), match.end()))
            
            if not positions:
                return self.truncate_sentence(sentence, max_length)
            
            positions.sort()
            start_pos = positions[0][0]
            end_pos = positions[-1][1]
            context_length = (max_length - (end_pos - start_pos)) // 2
            
            start = max(0, start_pos - context_length)
            end = min(len(sentence), end_pos + context_length)
            
            if start > 0:
                start = sentence.rfind(' ', 0, start) + 1
            if end < len(sentence):
                end = sentence.rfind(' ', end) + 1
            
            truncated = sentence[start:end].strip()
            if start > 0:
                truncated = '...' + truncated
            if end < len(sentence):
                truncated = truncated + '...'
            
            return truncated

        def extract_text_from_epub(file_path):
            book = epub.read_epub(file_path)
            full_text = ""
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                content = item.get_body_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                full_text += soup.get_text(separator=' ')
            return full_text

        def clean_linebreaks(text):
            return re.sub(r'(\n\s*)+', ' ', text).strip()

        # Pre-process keywords and their forms
        keyword_forms_map = {}
        for keyword in keywords:
            forms_list, exact_matches = self.get_keyword_forms(keyword)
            # Skip if all forms have been processed
            all_forms = [form.lower() for sublist in forms_list for form in sublist]
            if all(form in processed_keywords for form in all_forms):
                continue
            keyword_forms_map[keyword] = (forms_list, exact_matches, all_forms)

        unique_sentences = set()

        # Process each file once
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            
            # Extract metadata once per file if needed
            metadata = None
            if metadata_settings:
                try:
                    metadata = self.get_book_metadata(file_path, metadata_prefix)
                except Exception as e:
                    print(f"Error extracting metadata from {filename}: {str(e)}")
                    metadata = filename
            
            # Read file content
            try:
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
                    print(f"Unsupported file type: {file_path}")
                    continue

                # Clean and split text into sentences
                full_text = clean_linebreaks(full_text)
                
                # Pre-filter keywords based on simple text matching
                active_keywords = {}
                for keyword, (forms_list, exact_matches, all_forms) in keyword_forms_map.items():
                    # Check if any form of the keyword appears in the text
                    if any(form.lower() in full_text.lower() for forms in forms_list for form in forms):
                        active_keywords[keyword] = (forms_list, exact_matches)

                if not active_keywords:
                    continue  # Skip processing if no keywords found in file

                # Process sentences only if we have matching keywords
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', full_text)
                
                for sentence in sentences:
                    sentence_cleaned = self.replace_broken_characters(sentence.strip())
                    
                    # Check each active keyword
                    for keyword, (forms_list, exact_matches) in active_keywords.items():
                        matched_sentence_trimmed = match_keywords(forms_list, exact_matches, sentence_cleaned, max_length)
                        if matched_sentence_trimmed:
                            if metadata_settings:
                                sentence_data = (matched_sentence_trimmed, file_path, metadata)
                            else:
                                sentence_data = (matched_sentence_trimmed, file_path)
                                
                            if sentence_data not in unique_sentences:
                                unique_sentences.add(sentence_data)
                                if keyword not in combined_sentences:
                                    combined_sentences[keyword] = []
                                combined_sentences[keyword].append(sentence_data)

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                continue

        # Update processed keywords
        for _, (_, _, all_forms) in keyword_forms_map.items():
            processed_keywords.extend(all_forms)

        print(f"Processed keywords: {processed_keywords[0:5]} ...")
        print(f"Extracted {len(unique_sentences)} unique sentences.")

########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################


    def create_directories(self):
        # Create the directories if they do not exist
        os.makedirs(self.presets_dir, exist_ok=True)
        os.makedirs(self.text_presets_dir, exist_ok=True)
        os.makedirs(self.session_presets_dir, exist_ok=True)
        os.makedirs(self.theme_presets_dir, exist_ok=True)  # Create the theme presets directory

        os.makedirs(self.rainmeter_presets_dir, exist_ok=True)  # Create the theme presets directory
        os.makedirs(self.rainmeter_deleted_files_dir, exist_ok=True)  # Create the theme presets directory

        print(f"Created directories: {self.presets_dir}, {self.text_presets_dir}, {self.session_presets_dir}, {self.theme_presets_dir}, {self.rainmeter_presets_dir}, {self.rainmeter_deleted_files_dir}")


    def save_session_presets(self):
        """Saves session details into a separate text file for each session."""
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
        """Deletes the selected preset file by sending it to the Recycle Bin and updates the preset table."""
        # Get the selected row
        selected_row = self.table_sentences_selection.currentRow()

        # Check if a row is actually selected
        if selected_row == -1:
            print('Warning', 'No preset selected for deletion.')
            return

        # Get the file name from the name column of the selected row
        file_item = self.table_sentences_selection.item(selected_row, 1)  # Column index 1 for name
        if not file_item:
            self.show_info_message('Warning', 'No file associated with the selected preset.')
            return

        file_name = file_item.text() + ".txt"
        file_path = os.path.join(self.text_presets_dir, file_name)

        # Move the file to the Recycle Bin if it exists
        if os.path.exists(file_path):
            try:
                send2trash(file_path)
                
                # Remove from preset_labels_dictionary if it exists
                if file_name in self.preset_labels_dictionary:
                    del self.preset_labels_dictionary[file_name]
                    self.save_session_settings()  # Save the updated label assignments
                    
            except Exception as e:
                self.show_info_message('Error', f'Failed to send preset to Recycle Bin. Error: {str(e)}')
                return
        else:
            self.show_info_message('Warning', f'File "{file_name}" does not exist.')

        # Reload the presets
        self.load_presets()


        # After deletion, select the new last row if the table isn't empty
        if self.table_sentences_selection.rowCount() > 0:
            new_selected_row = self.table_sentences_selection.rowCount() - 1
            self.table_sentences_selection.selectRow(new_selected_row)
            self.update_selection_cache()



    def create_rainmeter_preset(self):
        """Create a Rainmeter preset based on the selected sentence preset."""
        # Get the selected row
        self.init_styles()
        selected_row = self.table_sentences_selection.currentRow()

        # Check if a row is actually selected
        if selected_row == -1:
            self.show_info_message('Warning', 'No preset selected.')
            return

        # Get the file name from the first column of the selected row
        file_item = self.table_sentences_selection.item(selected_row, 0)
        if not file_item:
            self.show_info_message('Warning', 'No file associated with the selected preset.')
            return

        # Construct the preset name
        preset_name = file_item.text()
        preset_folder_name = f"rainmeter_text_{preset_name}"

        # Determine the base directory based on whether the app is running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            temp_dir = sys._MEIPASS
            self.rainmeter_files_dir = os.path.join(temp_dir, 'rainmeter_files')
        else:
            self.rainmeter_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rainmeter_files')

        # Define the destination path
        destination_folder = os.path.join(self.rainmeter_presets_dir, preset_folder_name)

        # Remove the existing folder if it exists
        if os.path.exists(destination_folder):
            for root, dirs, files in os.walk(destination_folder, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(destination_folder)

        # Create the destination folder
        os.makedirs(destination_folder, exist_ok=True)

        # Define file paths
        ini_file_source = os.path.join(self.rainmeter_files_dir, "TEXT_SLIDESHOW.ini")
        lua_file_source = os.path.join(self.rainmeter_files_dir, "TEXT_SLIDESHOW.lua")
        ini_file_destination = os.path.join(destination_folder, "TEXT_SLIDESHOW.ini")
        lua_file_destination = os.path.join(destination_folder, "TEXT_SLIDESHOW.lua")
        rich_text_file_source = os.path.join(self.rainmeter_files_dir, "rich_text_copy.py")
        rich_text_file_destination = os.path.join(destination_folder, "rich_text_copy.py")


        def rgb_to_rgba(rgb_str):
            # Use regex to extract the RGB values, allowing optional spaces after commas
            match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_str)
            if match:
                # Extract the RGB values and convert them to integers
                r, g, b = map(int, match.groups())
                # Return the RGBA string with alpha value 255
                return f"{r}, {g}, {b}, 255"
            else:
                raise ValueError("Invalid RGB format")

        def luminance(text_color):
            # Parse the string to extract the RGB values
            text_color = tuple(map(int, text_color.replace(" ", "").split(',')))

            r, g, b, a = text_color
            # Calculate luminance using the formula
            luminance_value = 0.2126 * r + 0.7152 * g + 0.0722 * b
            # Determine the background color based on the luminance value
            if luminance_value > 127.5:  # If the color is bright enough
                return "0, 0, 0, 180"  # Dark background
            else:
                return "255, 255, 255, 225"  # Light background

        try:
            # Copy the Lua file without modifications
            if os.path.exists(lua_file_source):
                with open(lua_file_source, 'rb') as src:
                    with open(lua_file_destination, 'wb') as dst:
                        dst.write(src.read())
            else:
                raise FileNotFoundError(f"Lua file not found at {lua_file_source}")

            # Copy the rich_text file without modifications
            if os.path.exists(rich_text_file_source):
                with open(rich_text_file_source, 'rb') as src:
                    with open(rich_text_file_destination, 'wb') as dst:
                        dst.write(src.read())
            else:
                raise FileNotFoundError(f"Rich text copy file not found at {rich_text_file_source}")

            # Read and modify the INI file
            if os.path.exists(ini_file_source):
                with open(ini_file_source, "r") as ini_file:
                    ini_content = ini_file.read()

                # Replace placeholders in the INI file
                selected_preset_path = os.path.join(self.text_presets_dir, f"{preset_name}.txt")
                ini_content = ini_content.replace(r'TextPreset = TextPreset', r'TextPreset = ' + selected_preset_path)
                ini_content = ini_content.replace(r'DeletedFilesFolder = DeletedFilesFolder', r'DeletedFilesFolder =' + self.rainmeter_deleted_files_dir + '\\')

                ini_content = ini_content.replace(r'Title = Title', r'Title =' + f"{preset_name}")

                # Dynamic paths for rich text copy
                ini_content = ini_content.replace(r'Temp_file_path=Temp_file_path', r'Temp_file_path=' + self.rainmeter_presets_dir+ '\\temp_file_copy.txt')


                # Text colors from file
                ini_content = ini_content.replace(r'FontColor = FontColor', r'FontColor =' + f"{rgb_to_rgba(self.color_settings['text_color'])}")
                ini_content = ini_content.replace(r'BracketColor1 = BracketColor1', r'BracketColor1 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_1'])}")
                ini_content = ini_content.replace(r'BracketColor2 = BracketColor2', r'BracketColor2 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_2'])}")
                ini_content = ini_content.replace(r'BracketColor3 = BracketColor3', r'BracketColor3 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_3'])}")
                ini_content = ini_content.replace(r'BracketColor4 = BracketColor4', r'BracketColor4 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_4'])}")
                ini_content = ini_content.replace(r'BracketColor5 = BracketColor5', r'BracketColor5 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_5'])}")
                ini_content = ini_content.replace(r'BracketColor6 = BracketColor6', r'BracketColor6 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_6'])}")
                ini_content = ini_content.replace(r'BracketColor7 = BracketColor7', r'BracketColor7 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_7'])}")
                ini_content = ini_content.replace(r'BracketColor8 = BracketColor8', r'BracketColor8 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_8'])}")
                ini_content = ini_content.replace(r'BracketColor9 = BracketColor9', r'BracketColor9 =' + f"{rgb_to_rgba(self.color_settings['highlight_color_9'])}")



                background_color = luminance(rgb_to_rgba(self.color_settings['text_color']))
                ini_content = ini_content.replace(r'Backgroundcolor = Backgroundcolor', r'Backgroundcolor = ' + f"{background_color}")

                

                # Write the modified content to the destination INI file
                with open(ini_file_destination, "w") as ini_file:
                    ini_file.write(ini_content)
            else:
                raise FileNotFoundError(f"INI file not found at {ini_file_source}")

            # Open File Explorer and select the newly created folder
            subprocess.run(["explorer", "/select,", os.path.abspath(destination_folder)])

            self.show_info_message("Success", f'Rainmeter preset "{preset_folder_name}" created successfully!')

        except Exception as e:
            self.show_info_message("Error", f"Failed to create Rainmeter preset. Error: {str(e)}")


    def delete_presets_files(self):
        """Deletes the selected preset file by sending it to the Recycle Bin and updates the preset table."""
        # Get the selected row
        selected_row = self.table_session_selection.currentRow()
        
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
        
        # Move the file to the Recycle Bin if it exists
        if os.path.exists(file_path):
            try:
                send2trash(file_path)
            except Exception as e:
                self.show_info_message('Error', f'Failed to send preset to Recycle Bin. Error: {str(e)}')
                return
        else:
            self.show_info_message('Warning', f'File "{file_name}" does not exist.')
        
        # Reload the presets
        self.load_presets()
        
        # After deletion, select the new last row if the table isn't empty
        if self.table_session_selection.rowCount() > 0:
            # Select the last row (rowCount() - 1)
            new_selected_row = self.table_session_selection.rowCount() - 1
            self.table_session_selection.selectRow(new_selected_row)
            # Update the selection cache
            self.update_selection_cache()

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

        print("-- Renaming file")
        try:
            # Determine which table triggered the rename
            if item.tableWidget() == self.table_sentences_selection:
                cache = self.sentence_names_cache
                rename_directory = self.text_presets_dir
                name_col_index = 1
            elif item.tableWidget() == self.table_session_selection:
                cache = self.session_names_cache
                rename_directory = self.session_presets_dir
                name_col_index = 0
            else:
                # Unexpected table widget, exit early
                return False
                
            row = item.row()
            if row >= len(cache):
                return False

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
                return False

            # Check if the new filename already exists or if it is invalid
            if os.path.exists(new_filepath):
                self.show_info_message('Error', f"Cannot rename: '{new_filename}' already exists.")
                return False

            # Rename the file
            os.rename(old_filepath, new_filepath)

            # Update label assignment if this is a sentence preset
            if item.tableWidget() == self.table_sentences_selection and old_filename in self.preset_labels_dictionary:
                label = self.preset_labels_dictionary[old_filename]
                del self.preset_labels_dictionary[old_filename]
                self.preset_labels_dictionary[new_filename] = label
            
            # Update the cache after renaming
            cache[row] = new_filename
            
            # Save settings to persist label changes
            self.save_session_settings()
            
            return True

        except Exception as e:
            self.show_info_message('Error', f"Failed to rename preset. Error: {str(e)}")
            return False






    def load_presets(self):
        """Load existing presets into the tables and apply row selection from already loaded settings."""
        # Block signals during reload
        self.table_sentences_selection.blockSignals(True)
        self.table_session_selection.blockSignals(True)
        
        try:
            # Load sentence presets
            self.load_table_sentences_selection()
            
            # Load session presets
            self.load_session_presets()
            
            # Apply row selections after tables are loaded
            selected_sentence_row = self.selected_sentence_row
            selected_session_row = self.selected_session_row
            
            # Apply sentence selection
            if 0 <= selected_sentence_row < self.table_sentences_selection.rowCount():
                self.table_sentences_selection.selectRow(selected_sentence_row)
                self.sentence_selection_cache = selected_sentence_row
            
            # Apply session selection
            if 0 <= selected_session_row < self.table_session_selection.rowCount():
                self.table_session_selection.selectRow(selected_session_row)
        finally:
            # Always unblock signals when done
            self.table_sentences_selection.blockSignals(False)
            self.table_session_selection.blockSignals(False)
            # Manually update cache once at the end
            self.update_selection_cache()



    # Add new method to open the label manager
    def open_label_manager(self):
        """Open the label manager dialog."""
        dialog = LabelManagerDialog(self, self.labels_color_dictionary)
        self.init_styles(dialog=dialog)
        if dialog.exec_():
            self.labels_color_dictionary = dialog.get_labels()

            self.save_session_settings()  # Save the updated label settings
            self.load_presets()  # Reload with new labels



    def load_table_sentences_selection(self):
        """Load sentence preset files into the sentences presets table and update the cache, including label colors."""
        # Store currently selected filename before clearing (if any)
        self.table_sentences_selection.blockSignals(True)
        try:


            selected_filename = getattr(self, 'selected_sentence_filename', None)
            print("selected_sentence_filename : " , selected_filename)


            # Temporarily disable sorting to prevent issues during loading
            was_sorting_enabled = self.table_sentences_selection.isSortingEnabled()
            self.table_sentences_selection.setSortingEnabled(False)
            
            # Clear the table
            self.table_sentences_selection.setRowCount(0)
            
            # Load files from cache or directory
            self.sentence_names_cache = []
            try:
                files = sorted(os.listdir(self.text_presets_dir))
            except FileNotFoundError:
                files = []

            # Set up table with 3 columns: Label, Name and Sentences
            self.table_sentences_selection.setColumnCount(3)
            self.table_sentences_selection.setHorizontalHeaderLabels(['Label', 'Name', 'Sentences'])
            
            # Set column widths
            self.table_sentences_selection.setColumnWidth(0, 40)  # Label column width
            self.table_sentences_selection.setColumnWidth(1, 295)  # Name column width
            self.table_sentences_selection.setColumnWidth(2, 80)  # Sentences column width

            # Dictionary to map labels to sort order prefixes (01_, 02_, etc.)
            ordered_labels = self.get_ordered_labels_from_settings()
            label_sort_prefixes = {}
            
            # Create sort prefixes based on the order in settings (01_, 02_, etc.)
            for i, label in enumerate(ordered_labels):
                # Use two digits with leading zero for better sorting
                prefix = f"{i+1:02d}_"
                label_sort_prefixes[label] = prefix

            table_delegate = TableLabelDelegate(self.table_sentences_selection)
            self.table_sentences_selection.setItemDelegateForColumn(0, table_delegate)

            max_length_delegate = MaxLengthDelegate(max_length=60)
            self.table_sentences_selection.setItemDelegateForColumn(1, max_length_delegate)

            # Prevent column resizing for table_sentence_selection
            header_images = self.table_sentences_selection.horizontalHeader()
            header_images.setSectionResizeMode(QHeaderView.Fixed)
            header_images.setSectionsClickable(True)  # Make header non-clickable


            # Create a mapping of filenames to row positions
            filename_to_row = {}
            
            
            for filename in files:
                if filename.endswith(".txt"):
                    # Get display name (remove .txt extension)
                    display_name = os.path.splitext(filename)[0]
                    
                    # Insert item into the sentence presets table
                    row_position = self.table_sentences_selection.rowCount()
                    self.table_sentences_selection.insertRow(row_position)

                    # Store mapping of filename to row position
                    filename_to_row[filename] = row_position
                    

                    # Get label color and sort prefix for this preset
                    label_name = self.preset_labels_dictionary.get(filename, "Default")
                    label_color = self.labels_color_dictionary.get(label_name, "#00000000")
                    sort_prefix = label_sort_prefixes.get(label_name, "99_")  # Use high prefix for undefined labels

                    # Add color label with hidden sort text
                    color_item = QtWidgets.QTableWidgetItem(sort_prefix)
                    color_item.setBackground(QColor(label_color))
                    color_item.setToolTip(label_name)
                    color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
                    self.table_sentences_selection.setItem(row_position, 0, color_item)


                    # Add name item (Column 1)
                    name_item = QtWidgets.QTableWidgetItem(display_name)
                    name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                    self.table_sentences_selection.setItem(row_position, 1, name_item)


                    # Count the number of empty lines in the text file
                    file_path = os.path.join(self.text_presets_dir, filename)
                    empty_line_count = 0
                    
                    try:
                        # Try UTF-8 first, fall back to other encodings if needed
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                for line in file:
                                    if line.strip() == "":  # Check for empty line
                                        empty_line_count += 1
                        except UnicodeDecodeError:
                            # Try ISO-8859-1 if UTF-8 fails
                            with open(file_path, 'r', encoding='iso-8859-1') as file:
                                for line in file:
                                    if line.strip() == "":  # Check for empty line
                                        empty_line_count += 1
                    except Exception as e:
                        print(f"Error reading file {filename}: {str(e)}")
                        empty_line_count = 0  # Set to 0 if we can't read the file

                    # Add the empty line count to the third column
                    count_item = QtWidgets.QTableWidgetItem(str(empty_line_count))
                    count_item.setTextAlignment(QtCore.Qt.AlignCenter)  # Center the text
                    count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable

                    self.table_sentences_selection.setItem(row_position, 2, count_item)

                    # Update cache with the current filenames
                    self.sentence_names_cache.append(filename)

            # Re-enable sorting if it was enabled before
            self.table_sentences_selection.setSortingEnabled(was_sorting_enabled)
            
            # Restore selection using filename mapping
            if selected_filename in filename_to_row:
                self.table_sentences_selection.selectRow(filename_to_row[selected_filename])
                self.table_sentences_selection.setFocus()
            elif hasattr(self, 'selected_sentence_row') and 0 <= self.selected_sentence_row < self.table_sentences_selection.rowCount():
                # Fallback to row number if filename not found
                self.table_sentences_selection.selectRow(self.selected_sentence_row)
                self.table_sentences_selection.setFocus()

        finally:
            self.table_sentences_selection.blockSignals(False)


    def get_ordered_labels_from_settings(self):
        """
        Retrieve the ordered list of labels from settings.
        Implement this method to read the order from your settings file.
        """
        # Example implementation - replace with your actual code to read from settings
        # This should return a list of labels in the order they appear in your settings
        return list(self.labels_color_dictionary.keys())





    def load_session_presets(self):
        """Load session preset files with proper selection restoration."""

        self.table_session_selection.blockSignals(True)
        

        # Remember the currently selected filename before clearing
        selected_filename = getattr(self, 'selected_session_filename', None)
        try:
            # Temporarily disable sorting during loading
            was_sorting_enabled = self.table_session_selection.isSortingEnabled()
            self.table_session_selection.setSortingEnabled(False)
            
            # Clear the table
            self.table_session_selection.setRowCount(0)
            
            # Load files from cache or directory

            self.session_names_cache = []
            try:
                files = sorted(os.listdir(self.session_presets_dir))
            except FileNotFoundError:
                files = []
            
            # Set up table with 3 columns
            self.table_session_selection.setColumnCount(3)
            self.table_session_selection.setHorizontalHeaderLabels(['Name', 'Sentences', 'Time'])
            
            # Set column widths
            self.table_session_selection.setColumnWidth(0, 380)
            self.table_session_selection.setColumnWidth(1, 60)
            self.table_session_selection.setColumnWidth(2, 20)
        

            # Set item delegates and header settings for table
            max_length_delegate = MaxLengthDelegate(max_length=60)

            self.table_session_selection.setItemDelegateForColumn(1, max_length_delegate)
            # Prevent column resizing for table_session_selection


            header_session = self.table_session_selection.horizontalHeader()
            header_session.setSectionResizeMode(QHeaderView.Fixed)
            header_session.setSectionsClickable(True)  # Make header non-clickable


            # Ensure the selection behavior is correctly set after applying styles
            self.table_session_selection.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.table_session_selection.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)



            # Create a mapping of filenames to row positions
            filename_to_row = {}
            
            # Load files into table rows
            for filename in files:
                if filename.endswith(".txt"):
                    # Get display name (remove .txt extension)
                    display_name = os.path.splitext(filename)[0]
                    
                    # Insert new row
                    row_position = self.table_session_selection.rowCount()
                    self.table_session_selection.insertRow(row_position)
                    
                    # Store mapping of filename to row position
                    filename_to_row[filename] = row_position
                    
                    # Add name item (Column 0)
                    name_item = QtWidgets.QTableWidgetItem(display_name)
                    name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                    self.table_session_selection.setItem(row_position, 0, name_item)
                    
                    # Load session data from file
                    file_path = os.path.join(self.session_presets_dir, filename)
                    total_sentences = 0
                    time_str = "0m 0s"
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            total_sentences = session_data.get("total_sentences", 0)
                            minutes = session_data.get("minutes", 0)
                            seconds = session_data.get("seconds", 0)
                            time_str = f"{minutes}m {seconds}s"
                    except:
                        pass
                    
                    # Add sentence count (Column 1)
                    count_item = QtWidgets.QTableWidgetItem(str(total_sentences))
                    count_item.setTextAlignment(QtCore.Qt.AlignCenter)
                    count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
                    self.table_session_selection.setItem(row_position, 1, count_item)
                    
                    # Add time string (Column 2)
                    time_item = QtWidgets.QTableWidgetItem(time_str)
                    time_item.setTextAlignment(QtCore.Qt.AlignCenter)
                    time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                    self.table_session_selection.setItem(row_position, 2, time_item)
                    
                    # Cache the filename
                    self.session_names_cache.append(filename)
            
            # Re-enable sorting if it was enabled before
            self.table_session_selection.setSortingEnabled(was_sorting_enabled)
            
            # Restore selection using filename mapping
            if selected_filename in filename_to_row:
                self.table_session_selection.selectRow(filename_to_row[selected_filename])
                self.table_session_selection.setFocus()
            elif hasattr(self, 'selected_session_row') and 0 <= self.selected_session_row < self.table_session_selection.rowCount():
                # Fallback to row number if filename not found
                self.table_session_selection.selectRow(self.selected_session_row)
                self.table_session_selection.setFocus()

        finally:
            self.table_session_selection.blockSignals(False)
 

    def start_session_launcher(self):
        self.save_session_settings()
        self.start_session_from_files()

    def start_session_from_files(self, sentence_preset_path=None, session_preset_path=None , randomize_settings=True):
        """
        Creates and runs SessionDisplay using information from the selected session and preset files.
        Handles both metadata and non-metadata sentence formats.
        """
        def convert_time_to_seconds(time_str):
            minutes, seconds = 0, 0
            if 'm' in time_str:
                minutes = int(time_str.split('m')[0])
                time_str = time_str.split('m')[1].strip()
            if 's' in time_str:
                seconds = int(time_str.split('s')[0])
            return minutes * 60 + seconds

        def parse_sentence_block(block):

            block = block.strip()
            try:
                # First try to parse as a list containing sentence and metadata
                entry = eval(block)
                if isinstance(entry, list) and len(entry) == 2:
                    return [entry[0].strip(), entry[1].strip()]
            except:
                # If parsing fails, treat as a regular sentence and add empty metadata
                return [block, ""]




        print("sentence_preset_path == None", sentence_preset_path)
        if sentence_preset_path == None:
            sentence_preset_path = os.path.join(self.text_presets_dir, self.selected_sentence_filename )
        if session_preset_path == None:
            session_preset_path = os.path.join(self.session_presets_dir, self.selected_session_filename )

        randomize_settings = self.randomize_settings


        session_details = {}
        selected_sentences = []


        try:
            with open(session_preset_path, 'r', encoding='utf-8') as f:
                session_details = json.load(f)
                print(f"Loaded session details from {session_preset_path}: {session_details}")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error reading session file: {session_preset_path}")
            return

        try:
            with open(sentence_preset_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                sentence_blocks = content.split("\n\n")
                for block in sentence_blocks:
                    try:
                        parsed_entry = parse_sentence_block(block)
                        selected_sentences.append(parsed_entry)
                    except Exception as e:
                        print(f"Failed to parse block: {block}, Error: {e}")
                print(f"Loaded {len(selected_sentences)} sentence blocks from {sentence_preset_path}.")
        except FileNotFoundError:
            print(f"Text file not found: {sentence_preset_path}")
            return

        # Use provided or default randomize_settings


        if randomize_settings:
            random.shuffle(selected_sentences)
            print("-- Sentences have been shuffled randomly.")


        session_time = convert_time_to_seconds(session_details.get('time', '0m 0s'))
        total_sentences_to_display = session_details.get('total_sentences', len(selected_sentences))

        if total_sentences_to_display > len(selected_sentences):
            print(f"Warning: Not enough sentences to display. Requested {total_sentences_to_display}, but only {len(selected_sentences)} available.")
            total_sentences_to_display = len(selected_sentences)

        selected_sentences = selected_sentences[:total_sentences_to_display]

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
            self.display.close()
            self.display = None

        self.display = SessionDisplay(
            file_path=sentence_preset_path,
            shortcuts=self.shortcut_settings,
            schedule=self.session_schedule,
            items=selected_sentences,
            total=self.total_scheduled_sentences,
            autocopy_settings=self.autocopy_settings,
            themes_dir=self.theme_presets_dir,
            current_theme=self.current_theme
        )
        self.init_styles(session=self.display)

        self.display.load_entry()
        self.display.show()




    def load_session_settings(self):
        session_settings_path = os.path.join(self.presets_dir, 'session_settings.txt')

        # Default settings - now including labels
        default_settings = {
            "selected_sentence_row": -1,
            "selected_session_row": -1,
            "selected_sentence_filename": None,
            "selected_session_filename": None,
            "randomize_settings": False,
            "auto_start_settings": False,
            "autocopy_settings": False,
            "theme_settings": 'default_theme.txt',
            "shortcuts": self.default_shortcuts,
            "keyword_method": "Method 1: Dictionary Presets",
            "dictionary_settings": {str(i): {"enabled": False, "path": ""} for i in range(10)},
            "labels_color_dictionary": {"Default": "#00000000"},
            "preset_labels_dictionary": {},
            "sentence_names_cache": [],
            "session_names_cache": []

        }

        # Initialize with default settings
        current_settings = default_settings.copy()

        # Load current settings if the file exists
        if os.path.exists(session_settings_path):
            try:
                with open(session_settings_path, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                    
                    # Merge settings while preserving default structure
                    for key in default_settings:
                        if key in file_settings:
                            if key == "dictionary_settings":
                                # Special merge for dictionary settings
                                for i in range(10):
                                    if str(i) in file_settings["dictionary_settings"]:
                                        current_settings["dictionary_settings"][str(i)] = {
                                            "enabled": file_settings["dictionary_settings"][str(i)].get("enabled", False),
                                            "path": file_settings["dictionary_settings"][str(i)].get("path", "")
                                        }
                            elif key in ["labels_color_dictionary", "preset_labels_dictionary"]:
                                # Direct assignment for dictionaries
                                current_settings[key] = file_settings[key]
                            else:
                                current_settings[key] = file_settings[key]
                    
            except Exception as e:
                print(f"Error loading session settings: {str(e)}. Using default settings.")

        # Apply settings to instance variables
        self.shortcut_settings = current_settings["shortcuts"]
        self.randomize_settings = current_settings["randomize_settings"]
        self.auto_start_settings = current_settings["auto_start_settings"]
        self.autocopy_settings = current_settings["autocopy_settings"]
        self.current_theme = current_settings["theme_settings"]
        self.keyword_method = current_settings.get("keyword_method", "Method 1: Dictionary Presets")
        self.dictionary_settings = current_settings["dictionary_settings"]
        self.labels_color_dictionary = current_settings["labels_color_dictionary"]
        self.preset_labels_dictionary = current_settings["preset_labels_dictionary"]

        # Apply UI settings
        self.randomize_toggle.setChecked(self.randomize_settings)
        self.auto_start_toggle.setChecked(self.auto_start_settings)
        self.autocopy_toggle.setChecked(self.autocopy_settings)


        # Row selection logic
        self.selected_sentence_row = current_settings["selected_sentence_row"]
        self.selected_session_row = current_settings["selected_session_row"]


        self.selected_sentence_filename = current_settings["selected_sentence_filename"]
        self.selected_session_filename = current_settings["selected_session_filename"]

        # Initialize caches if they exist in settings
        if "sentence_names_cache" in current_settings:
            self.sentence_names_cache = current_settings["sentence_names_cache"]
        if "session_names_cache" in current_settings:
            self.session_names_cache = current_settings["session_names_cache"]


    def save_session_settings(self):
        """Save session settings including labels"""
        print("---Saving settings---")

        session_settings_path = os.path.join(self.presets_dir, 'session_settings.txt')
        
        # Get current selections by filename
        selected_sentence_filename = None
        selected_session_filename = None


        # Get sentence selection
        selected_sentence_row = self.table_sentences_selection.currentRow()
        if selected_sentence_row >= 0:
            name_item = self.table_sentences_selection.item(selected_sentence_row, 1)
            if name_item:
                selected_sentence_filename = name_item.text() + ".txt"
        
        # Get session selection
        selected_session_row = self.table_session_selection.currentRow()
        if selected_session_row >= 0:
            name_item = self.table_session_selection.item(selected_session_row, 0)
            if name_item:
                selected_session_filename = name_item.text() + ".txt"



        # Update settings
        settings = {
            "selected_sentence_row": selected_sentence_row,  # Keep for backward compatibility
            "selected_session_row": selected_session_row,  # Keep for backward compatibility
            "selected_sentence_filename": selected_sentence_filename,
            "selected_session_filename": selected_session_filename,
            "randomize_settings": self.randomize_settings,
            "auto_start_settings": self.auto_start_settings,
            "autocopy_settings": self.autocopy_settings,
            "theme_settings": self.current_theme,
            "shortcuts": self.shortcut_settings,
            "labels_color_dictionary": self.labels_color_dictionary,
            "preset_labels_dictionary": self.preset_labels_dictionary,
            "sentence_names_cache": self.sentence_names_cache if hasattr(self, 'sentence_names_cache') else [],
            "session_names_cache": self.session_names_cache if hasattr(self, 'session_names_cache') else []
        }

        # Save to file
        try:
            with open(session_settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving session settings: {str(e)}")


    def apply_shortcuts_main_window(self):
        """Apply the shortcuts for the main window."""

        self.main_window_start_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcut_settings["main_window"]["start"]), self)
        self.main_window_start_shortcut.activated.connect(self.start_session_launcher)

        self.main_window_close_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcut_settings["main_window"]["close"]), self)
        self.main_window_close_shortcut.activated.connect(self.close)

        self.main_window_cycle_label = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcut_settings["main_window"]["cycle_label"]), self)
        self.main_window_cycle_label.activated.connect(self.cycle_label)




    def cycle_label(self):
        selected_row = self.table_sentences_selection.currentRow()
        if selected_row >= 0:
            # Get the selected file name
            file_item = self.table_sentences_selection.item(selected_row, 1)  # Name column
            if file_item:
                filename = file_item.text() + ".txt"
                
                # Get all label names sorted
                label_names = sorted(list(self.labels_color_dictionary.keys()))
                
                # Get current label
                current_label = self.preset_labels_dictionary.get(filename, "Default")
                
                # Find next label in the sequence
                try:
                    current_index = label_names.index(current_label)
                    next_index = (current_index + 1) % len(label_names)
                    next_label = label_names[next_index]
                except ValueError:
                    # If current label not found (shouldn't happen unless corrupted data)
                    next_label = "Default"
                
                # Set the new label
                self.preset_labels_dictionary[filename] = next_label
                
                # Update the color cell
                color_item = self.table_sentences_selection.item(selected_row, 0)
                if color_item:
                    color = self.labels_color_dictionary.get(next_label, "#00000000")
                    color_item.setBackground(QColor(color))
                    color_item.setToolTip(next_label)

                # Save the settings & Reload table
                self.save_session_settings()
                self.load_presets()


                return True  # Event handled



    def update_autocopy_settings(self, state):
        """Update the autocopy_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.autocopy_settings = True
        else:
            self.autocopy_settings = False

        self.save_session_settings()

    def update_randomize_settings(self, state):
        """Update the randomize_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.randomize_settings = True
        else:
            self.randomize_settings = False

        self.save_session_settings()


    def update_auto_start_settings(self, state):
        """Update the randomize_settings variable based on the checkbox state."""
        # Check if the checkbox is checked (Qt.Checked is 2, Qt.Unchecked is 0)
        if state == Qt.Checked:
            self.auto_start_settings = True
        else:
            self.auto_start_settings = False
        self.save_session_settings()




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


# Delegate for the main table's label column (column 0)
class TableLabelDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TableLabelDelegate, self).__init__(parent)
        
    def paint(self, painter, option, index):
        # Check if this is column 0 (the label column)
        if index.column() == 0:
            # Get the original background color stored in the item
            color = index.data(Qt.BackgroundRole)
            
            # If the item is selected, we still want to show some indication
            if option.state & QStyle.State_Selected:
                # Draw a border to indicate selection but keep the original background
                painter.save()
                painter.setPen(Qt.white)
                painter.fillRect(option.rect, color)
                painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
                painter.restore()
            else:
                # Not selected, just fill with the original color
                painter.fillRect(option.rect, color)
            
            return
        
        # For all other columns, use the default delegate painting
        super(TableLabelDelegate, self).paint(painter, option, index)

# Delegate for the label manager's color column (column 1)
class LabelColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(LabelColorDelegate, self).__init__(parent)
        
    def paint(self, painter, option, index):
        # Check if this is column 1 (the color column)
        if index.column() == 1:
            # Get the original background color stored in the item
            color = index.data(Qt.BackgroundRole)
            
            # If the item is selected, we still want to show some indication
            if option.state & QStyle.State_Selected:
                # Draw a border to indicate selection but keep the original background
                painter.save()
                painter.setPen(Qt.white)
                painter.fillRect(option.rect, color)
                painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
                painter.restore()
            else:
                # Not selected, just fill with the original color
                painter.fillRect(option.rect, color)
            
            return
        
        # For all other columns, use the default delegate painting
        super(LabelColorDelegate, self).paint(painter, option, index)


class SessionDisplay(QWidget, Ui_session_display):
    closed = QtCore.pyqtSignal() # Needed here for close event to work.

    def __init__(self, file_path=None, shortcuts=None, schedule=None, items=None, total=None, autocopy_settings=None, themes_dir=None, current_theme=None):
        super().__init__()
        self.setupUi(self)

        # Add metadata display setting
        self.display_metadata = True  # New setting for metadata display

        # Initialize grid state
        self.setWindowTitle('Practice')

        # Install event filter on the QLineEdit
        self.lineEdit.installEventFilter(self)

        self.default_themes_dir = themes_dir
        self.current_theme=current_theme


        # Initialize text settings dictionary with default values

        self.load_text_display_settings()
        self.apply_lineedit_styles()
        # Init color settings
        self.color_settings = {}


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
        self.playlist = items if items else []
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
        self.autocopy_settings = autocopy_settings

        if autocopy_settings:
            self.clipboard_button.setChecked(True)


    # Method to load settings from the theme file
    def load_text_display_settings(self):
        # Construct the path to the theme file
        theme_file_path = os.path.join(self.default_themes_dir, self.current_theme)

        # Check if the theme file exists
        if not os.path.exists(theme_file_path):
            print(f"Theme file '{theme_file_path}' not found.")
            return

        # Load the theme data (assuming it's a JSON file)
        try:
            with open(theme_file_path, 'r', encoding='utf-8') as theme_file:
                theme_data = json.load(theme_file)
        except Exception as e:
            print(f"Error loading theme file: {e}")
            return

        # Retrieve text display settings from the theme data
        text_display = theme_data.get('text_display', {})

        # Initialize text settings with values from the theme or defaults
        self.text_display_settings = {
            "font_size": text_display.get("font_size", 16),
            "font_family": text_display.get("font_family", "Arial"),
            "font_weight": text_display.get("font_weight", 50),
            "font_color": text_display.get("font_color", "black"),
            "font_size_lineedit": text_display.get("font_size_lineedit", 8),
            "font_family_lineedit": text_display.get("font_family_lineedit", "Arial"),
            "font_weight_lineedit": text_display.get("font_weight_lineedit", 50),
            "font_color_lineedit": text_display.get("font_color_lineedit", "black"),
            "max_length_lineedit": text_display.get("max_length_lineedit", 500),
        }

        # Optionally, you can check for other settings (highlight colors, metadata settings) if needed
        print("Text display settings loaded from theme:")
        print(self.text_display_settings)


    def apply_lineedit_styles(self):
        """
        Applies font settings and color to the lineEdit field based on the loaded theme.
        """
        # Apply font family, weight, and size
        line_edit_font = self.lineEdit.font()
        line_edit_font.setFamily(self.text_display_settings["font_family_lineedit"])
        line_edit_font.setWeight(self.text_display_settings["font_weight_lineedit"])
        line_edit_font.setPointSize(self.text_display_settings["font_size_lineedit"])

        # Apply font color
        line_edit_color = self.text_display_settings["font_color_lineedit"]
        self.lineEdit.setStyleSheet(f"color: {line_edit_color};")

        # Set the font for the lineEdit
        self.lineEdit.setFont(line_edit_font)
        
        # You can also adjust any other lineEdit properties as needed


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



    def highlight_keywords(self, sentence, display=True):
        """
        Highlights keywords with different font colors and weight:
        - Keywords between { and } are colored with different highlight colors depending on the number of curly braces.
        - The entire sentence is colored with self.text_color.

        :param sentence: The sentence to process.
        :param display: If True, highlights keywords; if False, returns the sentence without highlights.
        """
        if not display:
            # Remove highlight curly braces and return plain text
            sentence = re.sub(r'\{+(\w+?)\}+', r'\1', sentence)  # Remove {...}, {{...}}, etc.
            return sentence

        # Apply overall text color to the sentence
        sentence = rf'<span style="color:{self.color_settings["text_color"]};">{sentence}</span>'

        # Replace curly brackets with corresponding highlight color
        def replace_with_color(match):
            """Determine the color based on the number of curly braces and return the highlighted span."""
            # Count the number of opening braces
            curly_count = match.group(0).count('{')

            # Find the corresponding highlight color
            color_key = f"highlight_color_{curly_count}"
            color_style = self.color_settings.get(color_key, self.color_settings["highlight_color_1"])

            # Return the highlighted keyword wrapped in the appropriate color style
            return rf'<span style="color:{color_style}">{match.group(1)}</span>'

        # Use regex to find keywords with different levels of curly brackets and replace them
        sentence = re.sub(r'\{+(\w+?)\}+', replace_with_color, sentence)

        return sentence



    def copy_sentence(self, rich_text=True, metadata=False):
        """Copy the current sentence to the clipboard, with or without rich text."""
        # Parse the current sentence entry
        current_sentence, sentence_metadata = self.parse_sentence_entry(self.playlist[self.playlist_position])
        
        # Function to replace curly braces with appropriate highlighted spans
        def replace_with_color(match):
            curly_count = match.group(0).count('{')
            color_key = f"highlight_color_{curly_count}"
            color_style = self.color_settings.get(color_key, self.color_settings["highlight_color_1"])
            return rf'<span style="color:{color_style}">{match.group(1)}</span>'
        
        if metadata:
            metadata_text = f" - {sentence_metadata}" if sentence_metadata else ""
        else:
            metadata_text = ""
        
        if rich_text:
            text_color = self.color_settings.get('text_color', 'rgb(0, 255, 255)')
            highlighted_sentence = re.sub(r'\{+(\w+?)\}+', replace_with_color, current_sentence)
            highlighted_sentence = rf'<span style="color:{text_color}">{highlighted_sentence}</span>'
            
            # Add metadata if enabled
            highlighted_sentence_with_metadata = f"{highlighted_sentence}{metadata_text}" if metadata else highlighted_sentence
            
            # Add two empty lines to the HTML version
            highlighted_sentence_with_lines = f"{highlighted_sentence_with_metadata}<br><br><br>"
            
            clipboard = QApplication.clipboard()
            mime_data = QtCore.QMimeData()
            mime_data.setData('text/html', highlighted_sentence_with_lines.encode('utf-8'))
            
            plain_text = re.sub(r'\{+(\w+?)\}+', r'\1', current_sentence)
            plain_text_with_metadata = f"{plain_text}{metadata_text}" if metadata else plain_text
            
            # Add two empty lines to the plain text version
            plain_text_with_lines = f"{plain_text_with_metadata}\n\n\n"
            mime_data.setText(plain_text_with_lines)
            
            clipboard.setMimeData(mime_data)
            print(f"Copied Rich Text (HTML): {highlighted_sentence_with_lines}")
        else:
            clipboard_text = re.sub(r'\{+(\w+?)\}+', r'\1', current_sentence)
            clipboard_text_with_metadata = f"{clipboard_text}{metadata_text}" if metadata else clipboard_text
            
            # Add two empty lines to the plain text
            clipboard_text_with_lines = f"{clipboard_text_with_metadata}\n\n\n"
            
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text_with_lines)
            print(f"Copied Plain Text: {clipboard_text_with_lines}")



    def toggle_autocopy(self):
        if self.autocopy_settings:
            self.autocopy_settings = False
            self.clipboard_button.setChecked(False)
            print("Auto copy to clipboard : Off")
        else:
            self.autocopy_settings = True
            self.clipboard_button.setChecked(True)
            print("Auto copy to clipboard : On")


    def toggle_metadata(self):
        if self.display_metadata:
            self.display_metadata = False
            print("Metadata : Off")
        else:
            self.display_metadata = True
            print("Metadata : On")



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

    def sanitize_filename(self, name):
        """
        Sanitizes a string to make it safe for use as a filename.
        """
        return ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

    def remove_sentence(self):
        if not os.path.exists(self.file_path):
            print("File path does not exist.")
            return

        # Parse the current sentence and metadata
        current_sentence, current_metadata = self.parse_sentence_entry(
            self.playlist[self.playlist_position]
        )

        # Format the search string with properly escaped quotes
        search_string = f"\"\"\"{current_sentence}\"\"\""

        try:
            # Read the file content with proper encoding (utf-8 or other)
            with open(self.file_path, 'r', encoding='utf-8') as file:
                file_lines = file.readlines()
        except UnicodeDecodeError:
            # Handle the error if the file isn't encoded in utf-8
            print("Error: Unable to read the file with UTF-8 encoding. Trying a different encoding...")
            with open(self.file_path, 'r', encoding='cp1252') as file:
                file_lines = file.readlines()

        # Find and remove the exact line and the line beneath it (if empty)
        line_found = None
        updated_lines = []
        skip_next_line = False
        for line in file_lines:
            if skip_next_line:
                # Skip the next line if the previous one was removed and it is empty
                if line.strip() == "":
                    skip_next_line = False
                    continue

            if search_string in line:
                line_found = line.strip()  # Capture the exact line
                skip_next_line = True  # Flag to remove the next line if it is empty
                continue  # Skip the current line containing the search string

            updated_lines.append(line)

        if not line_found:
            print(search_string)
            print("Matching sentence not found in file.")
            return

        # Write updated lines back to the file
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)

        # Remove the current sentence from the playlist
        self.playlist.pop(self.playlist_position)
        self.playlist_position -= 1

        # Create a backup file with the removed line and metadata
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        truncated_sentence = current_sentence[:30].replace(" ", "")
        sanitized_sentence = self.sanitize_filename(truncated_sentence)
        unique_filename = f"{timestamp}_{sanitized_sentence}.txt"
        current_file_dir = os.path.dirname(self.file_path)
        new_file_path = os.path.join(current_file_dir, unique_filename)

        with open(new_file_path, 'w', encoding='utf-8') as new_file:
            new_file.write(f"{line_found}\n")

        send2trash(new_file_path)
        self.load_next_sentence()
        print(f"Sentence removed: '{current_sentence}' and saved to: '{new_file_path}' (sent to recycle bin)")

    def show_main_window(self):
        if view.isMinimized():  # Check if the window is minimized
            view.showNormal()  # Restore the window if minimized
        view.show()  # Show the main window
        view.init_styles()  # Initialize window style           
        view.raise_()  # Bring the window to the front
        view.activateWindow()  # Focus on the window

        
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
        self.copy_sentence_button.setToolTip(f"[{self.shortcuts['session_window']['copy_highlighted_text']}] Copy sentence to clipboard,\n[{self.shortcuts['session_window']['copy_highlighted_text_metadata']}] Copy sentence to clipboard with metadata,\n[{self.shortcuts['session_window']['copy_plain_text']}] Simple text copy,\n[{self.shortcuts['session_window']['copy_plain_text_metadata']}] Simple text copy with metadata")






        self.clipboard_button.clicked.connect(self.toggle_autocopy)
        self.clipboard_button.setToolTip(f"[{self.shortcuts['session_window']['toggle_autocopy']}] Automatically copy current sentence to clipboard")


        self.metadata_button.clicked.connect(self.toggle_metadata)
        self.metadata_button.setToolTip(f"[{self.shortcuts['session_window']['toggle_metadata']}] Toggle sentence's metadata")



        self.open_folder_button.clicked.connect(self.open_text_folder)
        self.open_folder_button.setToolTip(f"[{self.shortcuts['session_window']['open_folder']}] Open preset folder")

        self.delete_sentence_button.clicked.connect(self.remove_sentence)
        self.delete_sentence_button.setToolTip(f"[{self.shortcuts['session_window']['delete_sentence']}] Delete sentence")

        # Setting window
        self.show_main_window_button.clicked.connect(self.show_main_window)
        self.show_main_window_button.setToolTip(f"[{self.shortcuts['session_window']['show_main_window']}] Open settings window")


        # Open color picker
        self.color_text_button.clicked.connect(self.open_color_picker)
        self.color_text_button.setToolTip(f"[{self.shortcuts['session_window']['color_window']}] Open color window")

        
        
        


    def apply_shortcuts_session_window(self):

        """Apply the shortcuts for the session window."""
        self.toggle_highlight_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_highlight"]), self)
        self.toggle_highlight_key.activated.connect(self.toggle_highlight)


        self.toggle_text_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_text_field"]), self)
        self.toggle_text_key.activated.connect(self.toggle_text_field)


        self.color_text_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["color_window"]), self)
        self.color_text_key.activated.connect(self.open_color_picker)


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

        # Shortcut for copying as plain text (C)
        self.copy_plain_text_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_plain_text"]), self)
        self.copy_plain_text_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=False))


        # Shortcut for copying as plain text with metadata (Ctrl + Shift + C)
        self.copy_plain_text_metadata_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_plain_text_metadata"]), self)
        self.copy_plain_text_metadata_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=False,metadata=True))



        # Shortcut for copying as rich text (Ctrl + C)
        self.copy_rich_text_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_highlighted_text"]), self)
        self.copy_rich_text_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=True))
        
        # Shortcut for copying as rich text with metadata (Shift + C)
        self.copy_rich_text_metadata_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["copy_highlighted_text_metadata"]), self)
        self.copy_rich_text_metadata_shortcut.activated.connect(lambda: self.copy_sentence(rich_text=True,metadata=True))



        self.clipboard_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_autocopy"]), self)
        self.clipboard_key.activated.connect(self.toggle_autocopy)

        self.metadata_key = QtWidgets.QShortcut(QtGui.QKeySequence(self.shortcuts["session_window"]["toggle_metadata"]), self)
        self.metadata_key.activated.connect(self.toggle_metadata)

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
        # Apply main text settings
        font = QtGui.QFont()
        font.setPointSize(self.text_display_settings["font_size"])
        font.setFamily(self.text_display_settings.get("font_family", "Arial"))
        font.setWeight(self.text_display_settings.get("font_weight", QtGui.QFont.Normal))
        self.text_display.setFont(font)

        # Apply metadata text settings
        metadata_font = QtGui.QFont()
        metadata_font.setPointSize(self.color_settings['metadata_font_size'])
        metadata_font.setFamily(self.text_display_settings.get("font_family", "Arial"))
        self.metadata_label.setFont(metadata_font)
        self.metadata_label.setStyleSheet(f"color: {self.color_settings['text_color']};background: {self.color_settings['metadata_background']};padding: {self.color_settings['metadata_padding']};")

         #self.text_display.setStyleSheet(f"color: {self.color_settings['text_color']};")
        # Get RGB values for font color and background color
        #color = self.text_display_settings.get("font_color", "black")


    def parse_sentence_entry(self, entry):
        """
        Parse a sentence entry that contains both the sentence and metadata.
        Returns tuple of (sentence, metadata)
        """
        try:
            if isinstance(entry, list) and len(entry) == 2:
                return entry[0], entry[1]
            elif isinstance(entry, str):
                # Handle triple quotes by replacing them with single quotes
                entry = entry.replace('"""', '"')
                entry = eval(entry.strip())
                if isinstance(entry, list) and len(entry) == 2:
                    return entry[0], entry[1]
        except Exception as e:
            print(f"Error parsing entry: {entry}, Error: {e}")
        return str(entry).strip(), ""

    def display_sentence(self, update_status=True):
        if not hasattr(self, 'session_info') or sip.isdeleted(self.session_info):
            return

        if self.playlist_position >= len(self.playlist):
            self.display_end_screen()
            return

        current_sentence, metadata = self.parse_sentence_entry(self.playlist[self.playlist_position])

        self.session_info.setText(f'{self.playlist_position + 1}/{len(self.playlist)}')
        self.apply_text_settings()

        if self.highlight_toggle:
            displayed_sentence = self.highlight_keywords(current_sentence)
        else:
            displayed_sentence = self.highlight_keywords(current_sentence, display=False)
        self.text_display.setText(displayed_sentence)

        if self.display_metadata:
            self.metadata_label.setText(metadata)
            self.metadata_label.show()
        else:
            self.metadata_label.hide()

        if update_status:
            self.reset_timer()
        self.update_session_info()


        

    def update_border_overlay_geometry(self, event=None):
        # Update the geometry to cover the entire window
        self.border_overlay.setGeometry(self.rect())

        # Optionally redraw the border if it is currently shown
        if self.border_overlay.isVisible():
            self.apply_border(True)

    def apply_border(self, show_border=True, border_width=1):
        border_color = self.color_settings['always_on_top_border']  # Always present

        print('Border color:', border_color)

        if show_border:
            self.border_overlay.show()
            self.border_overlay.raise_()  # Ensure it's above all other widgets

            # Create a pixmap for the border overlay that matches the window size
            border_pixmap = QtGui.QPixmap(self.size())
            border_pixmap.fill(QtCore.Qt.transparent)  # Transparent background

            # Clean the RGB string by removing unwanted characters like semicolons
            border_color_clean = border_color.replace("rgb(", "").replace(")", "").replace(";", "")
            
            # Parse the cleaned RGB values into a QColor object
            rgb_values = [int(x) for x in border_color_clean.split(",")]
            q_color = QtGui.QColor(*rgb_values)

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




    def toggle_metadata(self):
        if self.display_metadata:
            self.display_metadata = False
            print("Metadata : Off")
        else:
            self.display_metadata = True
            print("Metadata : On")

        self.display_sentence()




    def open_color_picker(self):
        theme_file_path = os.path.join(self.default_themes_dir, self.current_theme)
        dialog_color = ColorPickerDialog(self, theme_file_path=theme_file_path, color_settings=self.color_settings)
        view.init_styles(dialog_color=dialog_color)

        if dialog_color.exec_():
            # After saving colors, update the color settings in the parent class (now all handled by color_settings)
            self.color_settings = dialog_color.parent().color_settings  # Directly update color_settings
            # Reapply the updated styles to the displayed sentence
            self.display_sentence()

        #view.init_styles(session_display=session_display)
        view.init_styles(session=view.display)
        self.apply_text_settings()





    def zoom_plus(self):
        """
        Increases the size of the session_display window, slightly increases the height of self.lineEdit,
        and also increases the font size, but within zoom limits.
        """
        current_size = self.size()
        max_size = QtCore.QSize(1600, 1200)  # Maximum window size
        current_font_size = self.text_display_settings["font_size_lineedit"]

        # Increase window size if below the maximum limit
        if current_size.width() < max_size.width() and current_size.height() < max_size.height():
            new_width = min(current_size.width() + 100, max_size.width())
            new_height = min(current_size.height() + 75, max_size.height())
            self.resize(new_width, new_height)

            # Increase lineEdit height
            line_edit_size = self.lineEdit.size()
            new_line_edit_height = min(line_edit_size.height() + 5, 50)  # Set a reasonable max height
            self.lineEdit.setFixedHeight(new_line_edit_height)

            # Increase font size to match the lineEdit height (within limits)
            new_font_size = min(current_font_size + 1, 18)  # Slight increase in font size, max 18
            self.text_display_settings["font_size_lineedit"] = new_font_size

            # Update the font size for self.lineEdit
            line_edit_font = self.lineEdit.font()
            line_edit_font.setPointSize(new_font_size)  # Set new font size
            self.lineEdit.setFont(line_edit_font)


    def zoom_minus(self):
        """
        Decreases the size of the session_display window, slightly decreases the height of self.lineEdit,
        and also decreases the font size, but within zoom limits.
        """
        current_size = self.size()
        min_size = QtCore.QSize(440, 200)  # Minimum window size
        current_font_size = self.text_display_settings["font_size_lineedit"]

        # Decrease window size if above the minimum limit
        if current_size.width() > min_size.width() and current_size.height() > min_size.height():
            new_width = max(current_size.width() - 100, min_size.width())
            new_height = max(current_size.height() - 75, min_size.height())
            self.resize(new_width, new_height)

            # Decrease lineEdit height
            line_edit_size = self.lineEdit.size()
            new_line_edit_height = max(line_edit_size.height() - 5, 20)  # Set a reasonable min height
            self.lineEdit.setFixedHeight(new_line_edit_height)

            # Decrease font size to match the lineEdit height (within limits)
            new_font_size = max(current_font_size - 1, 10)  # Slight decrease in font size, min 10
            self.text_display_settings["font_size_lineedit"] = new_font_size

            # Update the font size for self.lineEdit
            line_edit_font = self.lineEdit.font()
            line_edit_font.setPointSize(new_font_size)  # Set new font size
            self.lineEdit.setFont(line_edit_font)


    def reset_zoom(self):
        """
        Resets the window and font size to the default size.
        """
        default_size = QtCore.QSize(800, 600)  # Set your default window size
        self.resize(default_size)

        # Reset lineEdit height to default
        self.lineEdit.setFixedHeight(30)  # Set your default height

        # Reset font size to default
        default_font_size = 12  # Set your default font size
        self.text_display_settings["font_size_lineedit"] = default_font_size

        line_edit_font = self.lineEdit.font()
        line_edit_font.setPointSize(default_font_size)  # Set default font size
        self.lineEdit.setFont(line_edit_font)



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
        if self.autocopy_settings == True:
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

        if self.autocopy_settings == True:
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

        if self.autocopy_settings :
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

        # Set the text display to show the transparent image
        self.text_display.setPixmap(transparent_pixmap)
        self.metadata_label.hide()
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

class ColorPickerDialog(QDialog):
    def __init__(self, parent=None, color_settings=None, theme_file_path=None):
        super().__init__(parent)
        self.setWindowTitle("Pick Colors")
        # Remove the question mark from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # Set a wider window width
        self.resize(400, self.height())
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.color_settings = color_settings or {}
        self.theme_file_path = theme_file_path  # Store the theme file path

        # Load theme data if theme file path is provided
        if self.theme_file_path:
            self.load_colors()

        # Text color section - now first in the layout
        self.create_text_color_section()
        
        # Background Color Picker - now second in the layout, right after text color
        self.bg_label = QLabel("Background Color")
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setStyleSheet("padding: 5px;")
        
        self.bg_button = QPushButton()
        self.bg_button.setFixedSize(35, 35)
        self.bg_button.clicked.connect(self.pick_background_color)

        # Set initial background color from theme
        bg_color_str = self.color_settings.get("background", "rgb(240, 240, 240)")
        self.bg_color = self.parse_rgb_color(bg_color_str)
        self.update_bg_button()
        
        # Add background color widgets to main layout immediately after text color
        self.layout.addWidget(self.bg_label)
        self.layout.addWidget(self.bg_button, alignment=Qt.AlignCenter)
        
        # Highlight color section - now third in the layout
        self.create_highlight_color_section()

        # Save Button
        self.save_button = QPushButton("Save colors")
        self.save_button.clicked.connect(self.save_colors)
        self.layout.addWidget(self.save_button)
    
    def extract_background_color(self):
        """Extract background color from QWidget style in theme file."""
        try:
            with open(self.theme_file_path, "r") as file:
                theme_data = json.load(file)
            
            qwidget_style = theme_data["text_display"].get("QWidget", "")
            
            # Extract background color from style string
            if "background:" in qwidget_style:
                bg_parts = qwidget_style.split("background:")[1].split(";")[0].strip()
                return bg_parts
            return "rgb(240, 240, 240)"  # Default value
        except Exception as e:
            print(f"Error extracting background color: {e}")
            return "rgb(240, 240, 240)"  # Default value
    
    def parse_rgb_color(self, rgb_str):
        """Convert an RGB string like 'rgb(240, 240, 240)' to a QColor object."""
        try:
            rgb_values = [int(x.strip()) for x in rgb_str.replace("rgb(", "").replace(")", "").split(',')]
            return QColor(rgb_values[0], rgb_values[1], rgb_values[2])
        except Exception as e:
            print(f"Error parsing RGB color '{rgb_str}': {e}")
            return QColor(240, 240, 240)  # Default color on parsing error

    def pick_background_color(self):
        color = QColorDialog.getColor(self.bg_color, self)
        if color.isValid():
            self.bg_color = color
            self.update_bg_button()
            # Format the new background color in RGB format
            bg_rgb = f"rgb({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()})"
            # Save to color_settings for persistence
            self.color_settings["background"] = bg_rgb

    def update_bg_button(self):
        self.bg_button.setStyleSheet(f"background-color: {self.bg_color.name()};")

    def create_text_color_section(self):
        """Create an improved text color selection section."""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(10)  # Increased spacing for clarity

        # Text color label with improved styling
        text_label = QLabel("Text color :")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("padding: 5px;")

        # Text color button with enhanced appearance
        text_color_button = QPushButton()
        text_color_button.setObjectName("text_color_button")  # Set object name for findChild
        text_color_button.setFixedSize(35, 35)  # Slightly larger button for better usability
        
        # Get initial text color
        text_color_str = self.color_settings.get("text_color", "rgb(238, 238, 238)")
        text_color_button.setStyleSheet(f"background-color: {text_color_str}; border: none;")
        
        text_color_button.clicked.connect(lambda: self.pick_color("text_color", text_color_button))

        # Add widgets to layout
        section_layout.addWidget(text_label)
        section_layout.addWidget(text_color_button, alignment=Qt.AlignCenter)

        # Add to main layout
        self.layout.addLayout(section_layout)

    def get_text_color_based_on_background(self, background_color):
        """Determine whether the text color should be black or white based on the background color's brightness."""
        try:
            # Extract RGB values from the background color (assumes the format is 'rgb(r, g, b)')
            rgb_values = [int(x.strip()) for x in background_color[4:-1].split(',')]
            r, g, b = rgb_values

            # Calculate luminance using the formula
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

            # If luminance is greater than a certain threshold, use black text, else use white text
            return "black" if luminance > 128 else "white"
        except Exception as e:
            print(f"Error calculating text color: {e}")
            return "black"  # Default

    def create_highlight_color_section(self):
        """Create the highlight color section with buttons displayed in a grid."""
        section_layout = QVBoxLayout()

        # Highlight color label (centered)
        highlight_label = QLabel("Highlight Colors:")
        highlight_label.setAlignment(Qt.AlignCenter)
        highlight_label.setStyleSheet("padding: 5px;")

        # Create a grid layout for highlight color buttons
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(10)  # Increased vertical space for clarity

        # Create and add buttons to the grid layout
        for i in range(1, 10):
            highlight_key = f"highlight_color_{i}"
            color_button = QPushButton(str(i))  # Label with number (1, 2, ..., 9)
            color_button.setFixedSize(35, 35)  # Set size of buttons
            color_button.setObjectName(f"highlight_button_{i}")  # Set a unique object name

            # Get the button's background color
            background_color = self.color_settings.get(highlight_key, f"rgb(146,130,49)")

            # Get the text color based on the background color's brightness
            text_color = self.get_text_color_based_on_background(background_color)

            # Set the button's style with dynamic text color
            color_button.setStyleSheet(f"background-color: {background_color}; border: none; color: {text_color};")
            color_button.clicked.connect(lambda checked, k=highlight_key, btn=color_button: self.pick_color(k, btn))
            grid_layout.addWidget(color_button, (i-1)//3, (i-1)%3)  # Arrange in 3x3 grid

        # Create a group box for the grid layout to group the buttons
        group_box = QGroupBox()
        group_box.setLayout(grid_layout)
        group_box.setStyleSheet("border: none; background: transparent; padding: 10px;")  # Remove border and background

        # Add label and grid layout to the section layout
        section_layout.addWidget(highlight_label)
        section_layout.addWidget(group_box)

        # Add section layout to main layout
        self.layout.addLayout(section_layout)

    def pick_color(self, key, button):
        """Open color dialog to pick color for selected key and update the button background."""
        try:
            # Parse the current color string into a QColor object
            color_str = self.color_settings.get(key, "rgb(146,130,49)")
            color_parts = [int(val.strip()) for val in color_str.replace("rgb(", "").replace(")", "").split(",")]
            current_color = QColor(color_parts[0], color_parts[1], color_parts[2])

            # Open color dialog to pick color and set the current color as the initial selection
            new_color = QColorDialog.getColor(current_color, self, f"Pick a color for {key}")

            if new_color.isValid():
                # Update color in RGB format (not hex)
                self.color_settings[key] = f"rgb({new_color.red()}, {new_color.green()}, {new_color.blue()})"

                # Get the appropriate text color based on luminance
                text_color = self.get_text_color_based_on_background(self.color_settings[key])

                # Update the background color of the clicked button
                button.setStyleSheet(f"background-color: {self.color_settings[key]}; color: {text_color};")
        except Exception as e:
            print(f"Error picking color: {e}")

    def save_colors(self):
        """Save the selected colors into the theme file."""
        try:
            with open(self.theme_file_path, "r") as file:
                theme_data = json.load(file)
            
            # Get the current QWidget style
            qwidget_style = theme_data["text_display"].get("QWidget", "color: #00000000;padding: 0 30px;border: none")
            
            # Format the new background color in RGB format
            bg_rgb = f"rgb({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()})"
            
            # Update the background in the style string
            if "background:" in qwidget_style:
                # Split by "background:" and then by ";" to isolate the part we need to replace
                before_bg = qwidget_style.split("background:")[0]
                after_bg_parts = qwidget_style.split("background:")[1].split(";")
                after_bg = ";" + ";".join(after_bg_parts[1:]) if len(after_bg_parts) > 1 else ""
                
                # Construct the new QWidget style
                new_style = f"{before_bg}background: {bg_rgb}{after_bg}"
                theme_data["text_display"]["QWidget"] = new_style
            else:
                # If background is not in the style, add it
                theme_data["text_display"]["QWidget"] = qwidget_style + f";background: {bg_rgb}"
            
            # Update metadata_background to match the background color
            theme_data["text_display"]["metadata_background"] = bg_rgb
            
            # Save text color if it exists in color_settings
            if "text_color" in self.color_settings:
                theme_data["text_display"]["text_color"] = self.color_settings["text_color"]

            # Save highlight colors
            for i in range(1, 10):
                highlight_key = f"highlight_color_{i}"
                if highlight_key in self.color_settings:
                    theme_data["text_display"][highlight_key] = self.color_settings[highlight_key]

            # Save updated theme data to the file
            with open(self.theme_file_path, "w") as file:
                json.dump(theme_data, file, indent=4)

            # Debug output
            print(f"Background color saved: {bg_rgb}")
            print(f"Metadata background updated to match background: {bg_rgb}")
            print(f"QWidget style saved: {theme_data['text_display']['QWidget']}")
            
            # Update parent's color settings if parent exists
            if self.parent():
                if not hasattr(self.parent(), 'color_settings'):
                    self.parent().color_settings = {}
                self.parent().color_settings = self.color_settings.copy()
                print("Updated parent's color settings")
            
            self.accept()  # Close dialog after saving
            
        except Exception as e:
            print(f"Error saving colors: {e}")

    def load_colors(self):
        """Load colors from the theme file."""
        try:
            with open(self.theme_file_path, "r") as file:
                theme_data = json.load(file)
            
            # Initialize color_settings if it doesn't exist
            if not self.color_settings:
                self.color_settings = {}
            
            # Load QWidget style and extract background
            qwidget_style = theme_data["text_display"].get("QWidget", "")
            self.color_settings["QWidget"] = qwidget_style
            
            # Extract background color from QWidget style
            if "background:" in qwidget_style:
                bg_parts = qwidget_style.split("background:")[1].split(";")[0].strip()
                self.color_settings["background"] = bg_parts
                print(f"Loaded background color: {bg_parts}")
            else:
                self.color_settings["background"] = "rgb(240, 240, 240)"
                print("No background color found in QWidget style, using default")
            
            # Load text color
            self.color_settings["text_color"] = theme_data["text_display"].get("text_color", "rgb(238, 238, 238)")
            print(f"Loaded text color: {self.color_settings['text_color']}")

            # Load highlight colors
            for i in range(1, 10):
                highlight_key = f"highlight_color_{i}"
                self.color_settings[highlight_key] = theme_data["text_display"].get(highlight_key, "rgb(146,130,49)")

            # No need to update buttons here as they'll be created after this method is called
            
        except Exception as e:
            print(f"Error loading theme: {e}")
            # Set default values if file not found
            self.color_settings = {
                "background": "rgb(240, 240, 240)",
                "text_color": "rgb(238, 238, 238)"
            }
            # Set default highlight colors
            for i in range(1, 10):
                self.color_settings[f"highlight_color_{i}"] = "rgb(146,130,49)"

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
    def __init__(self, parent=None, preset_name="", text_presets_dir=None):
        super(MultiFolderSelector, self).__init__(parent)

        
        self.setWindowTitle("Select Files")

        self.setFixedSize(600, 780)  # This makes the window non-resizable

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        # Initialize selected files list
        self.selected_files = []
        self.text_presets_dir=text_presets_dir



        # Initialize keyword methods
        self.keyword_methods = ["Method 1: Dictionary Presets", "Method 2: Manual Search"]
        self.current_method = self.keyword_methods[0]
        

        # Main layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(10)  # Add some spacing between elements

        # File selection section (more compact)
        self.file_section = QtWidgets.QGroupBox("Selected Files")
        self.file_layout = QtWidgets.QVBoxLayout(self.file_section)
        
        # List widget for selected files
        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setToolTip("Selected files will be processed in order")
        self.list_widget.setMinimumHeight(100)  # Reduced height
        self.list_widget.setMaximumHeight(200)
        self.file_layout.addWidget(self.list_widget)


        # Preset Name Input with some spacing
        self.preset_name_edit = QtWidgets.QLineEdit(self)
        self.preset_name_edit.setPlaceholderText("Will be generated when files are selected")
        self.preset_name_edit.setText("")
        self.file_layout.addWidget(QtWidgets.QLabel("Preset Name:"))
        self.file_layout.addWidget(self.preset_name_edit)
        
        self.layout.addWidget(self.file_section)
        self.layout.addSpacing(10)  # Add space between sections


        # Method selection section
        self.method_section = QtWidgets.QGroupBox("Keyword Methods")
        self.method_layout = QtWidgets.QVBoxLayout(self.method_section)
        
        # Keyword Method Selection
        self.method_dropdown = QtWidgets.QComboBox(self)
        self.method_dropdown.addItems(self.keyword_methods)
        self.method_dropdown.currentIndexChanged.connect(self.change_keyword_method)
        self.method_layout.addWidget(self.method_dropdown)

        # Stacked widget for different methods
        self.method_stack = QtWidgets.QStackedWidget(self)
        self.method_stack.setMinimumHeight(350)  # More space for methods
        self.method_layout.addWidget(self.method_stack)

        # Method 1: Dictionary Presets
        self.method1_widget = QtWidgets.QWidget()
        self.method1_layout = QtWidgets.QVBoxLayout(self.method1_widget)
        
        self.dictionary_container = QtWidgets.QScrollArea()  # Add scroll area
        self.dictionary_container.setWidgetResizable(True)
        self.dictionary_content = QtWidgets.QWidget()
        self.dictionary_layout = QtWidgets.QVBoxLayout(self.dictionary_content)
        self.dictionary_layout.setContentsMargins(5, 5, 5, 5)
        
        self.dictionary_controls = []
        
        # Create highlight color controls (1-9)
        for i in range(1, 10):
            prefix = f"[{i}]"
            name = f"Highlight color {i}"
            
            control = {
                'checkbox': QtWidgets.QCheckBox(),
                'label': QtWidgets.QLabel(f"{prefix} {name}:"),
                'path_edit': QtWidgets.QLineEdit(),
                'browse_button': QtWidgets.QPushButton("Browse...")
            }
            
            control['path_edit'].setMinimumWidth(250)
            control['path_edit'].textChanged.connect(self.path_edited)
            control['browse_button'].clicked.connect(lambda _, idx=i: self.browse_dictionary_file(idx))

            control['checkbox'].setObjectName(f"dictionary_checkbox_{i}")
            control['label'].setObjectName(f"dictionary_label_{i}")
            control['path_edit'].setObjectName(f"dictionary_path_edit_{i}")
            control['browse_button'].setObjectName(f"dictionary_browse_button_{i}")

            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(control['checkbox'])
            hbox.addWidget(control['label'])
            hbox.addWidget(control['path_edit'], 1)
            hbox.addWidget(control['browse_button'])
            
            self.dictionary_layout.addLayout(hbox)
            self.dictionary_controls.append(control)
        
        # Separator before ignored keywords (more visible)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.dictionary_layout.addSpacing(10)
        self.dictionary_layout.addWidget(separator)
        self.dictionary_layout.addSpacing(10)
        
        # Ignored keywords control (0) - more prominent
        control = {
            'checkbox': QtWidgets.QCheckBox(),
            'label': QtWidgets.QLabel("[0] Ignored keywords:"),
            'path_edit': QtWidgets.QLineEdit(),
            'browse_button': QtWidgets.QPushButton("Browse...")
        }
        
        control['path_edit'].setMinimumWidth(250)
        control['path_edit'].textChanged.connect(self.path_edited)
        control['browse_button'].clicked.connect(lambda _, idx=0: self.browse_dictionary_file(idx))

        
        # Add object names
        control['checkbox'].setObjectName("dictionary_checkbox_0")
        control['label'].setObjectName("dictionary_label_0")
        control['path_edit'].setObjectName("dictionary_path_edit_0")
        control['browse_button'].setObjectName("dictionary_browse_button_0")

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(control['checkbox'])
        hbox.addWidget(control['label'])
        hbox.addWidget(control['path_edit'], 1)
        hbox.addWidget(control['browse_button'])
        
        self.dictionary_layout.addLayout(hbox)
        self.dictionary_controls.insert(0, control)
        
        self.dictionary_layout.addStretch()
        self.dictionary_container.setWidget(self.dictionary_content)
        self.method1_layout.addWidget(self.dictionary_container)
        self.method_stack.addWidget(self.method1_widget)

        # Method 2: Manual Search
        self.method2_widget = QtWidgets.QWidget()
        self.method2_layout = QtWidgets.QVBoxLayout(self.method2_widget)
        
        self.profile_dropdown = QtWidgets.QComboBox()
        self.profile_dropdown.addItems([f"Highlight color {i}" for i in range(1, 10)] + ["Ignored keywords"])
        self.profile_dropdown.currentIndexChanged.connect(self.change_manual_profile)
        self.method2_layout.addWidget(self.profile_dropdown)
        
        self.keyword_input = QtWidgets.QTextEdit()
        self.keyword_input.setPlaceholderText(
            "Enter keywords (one per line)\n\n"
            "\"Keyword\" : search for both singular and plural forms\n"
            "\"&Keyword\" : search the given form\n\n"
            "\"Keyword1 + Keyword2 + ...\" : search for both keywords, either forms\n"
            "\"&Keyword1 + &Keyword2 + ...\" : search for both keywords, given forms\n\n"
            "\"#Keyword\" : highlight the given form without searching it\n"
            "\";Comment\" : ignore the line or keyword"

        )        
        self.keyword_input.setMinimumHeight(250)
        self.method2_layout.addWidget(self.keyword_input)
        
        self.manual_profiles = {f"Highlight color {i}": [] for i in range(1, 10)}
        self.manual_profiles["Ignored keywords"] = []
        self.current_manual_profile = "Highlight color 1"
        
        self.method_stack.addWidget(self.method2_widget)
        self.method_stack.setCurrentIndex(0)
        
        self.layout.addWidget(self.method_section)


        # Max Length Input Field
        max_length_layout = QtWidgets.QHBoxLayout()
        self.max_length_label = QtWidgets.QLabel("Max Length:")
        max_length_layout.addWidget(self.max_length_label)
        self.max_length_edit = QtWidgets.QLineEdit()
        self.max_length_edit.setText("200")
        self.max_length_edit.setValidator(QtGui.QIntValidator(1, 10000, self))
        max_length_layout.addWidget(self.max_length_edit)
        self.layout.addLayout(max_length_layout)

        # Checkboxes
        self.highlight_keywords_checkbox = QtWidgets.QCheckBox("Highlight Keywords")
        self.highlight_keywords_checkbox.setChecked(True)
        self.layout.addWidget(self.highlight_keywords_checkbox)

        self.extract_metadata_checkbox = QtWidgets.QCheckBox("Extract Metadata")
        self.extract_metadata_checkbox.setChecked(True)
        self.layout.addWidget(self.extract_metadata_checkbox)

        # Output options
        self.output_option_dropdown = QtWidgets.QComboBox()
        self.output_option_dropdown.addItems(["Single output", "All output"])
        self.layout.addWidget(self.output_option_dropdown)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.add_files_button = QtWidgets.QPushButton("Add File(s)")
        self.add_files_button.clicked.connect(self.multi_select_files)
        button_layout.addWidget(self.add_files_button)

        self.remove_button = QtWidgets.QPushButton("Remove File")
        self.remove_button.clicked.connect(self.remove_file)
        button_layout.addWidget(self.remove_button)

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close_dialogue)
        button_layout.addWidget(self.cancel_button)

        self.layout.addLayout(button_layout)

        # Load initial settings
        self.load_dictionary_settings()


    def browse_dictionary_file(self, index):
        """Open file dialog to select dictionary file and auto-enable checkbox"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text Files (*.txt)")
        
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            if files:
                path = files[0]
                control = self.dictionary_controls[index]
                control['path_edit'].setText(self.format_path_display(path))  # Display shortened path
                control['path_edit'].setToolTip(path)  # Store full path as tooltip
                control['checkbox'].setChecked(True)  # Auto-enable the checkbox
                
                


    def path_edited(self):
        """Handle manual editing of path fields"""
        sender = self.sender()  # Get which QLineEdit was edited
        for control in self.dictionary_controls:
            if control['path_edit'] == sender:
                # Clear both display text and tooltip when empty
                if not sender.text().strip():
                    sender.setToolTip("")
                
                break


    def save_dictionary_settings(self):
        """Save only dictionary-related settings"""
        settings_path = os.path.join(self.parent().presets_dir, 'session_settings.txt')
        
        # Load existing settings first
        current_settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    current_settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {str(e)}")
                current_settings = {}

        # Update only the dictionary settings
        dictionary_settings = {}
        for i, control in enumerate(self.dictionary_controls):
            path = control['path_edit'].toolTip() or control['path_edit'].text()
            # Only save if path exists or is being explicitly cleared
            if not path.strip() or os.path.exists(path):
                dictionary_settings[str(i)] = {
                    'enabled': control['checkbox'].isChecked(),
                    'path': path if path.strip() else ""  # Ensure empty string for cleared paths
                }

        current_settings.update({
            "keyword_method": self.current_method,
            "dictionary_settings": dictionary_settings
        })
        
        # Save back to file
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=4)
        except Exception as e:
            print(f"Error saving dictionary settings: {str(e)}")


        #print("SAVING :",current_settings)

    def load_dictionary_settings(self):
        """Load only dictionary-related settings"""

        settings_path = os.path.join(self.parent().presets_dir, 'session_settings.txt')
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # Load keyword method
                    self.current_method = settings.get("keyword_method", self.keyword_methods[0])
                    self.method_dropdown.setCurrentText(self.current_method)
                    
                    # Load dictionary settings
                    if "dictionary_settings" in settings:
                        for i, control in enumerate(self.dictionary_controls):  # This includes index 0
                            if str(i) in settings["dictionary_settings"]:
                                cfg = settings["dictionary_settings"][str(i)]
                                control['checkbox'].setChecked(cfg.get('enabled', False))
                                full_path = cfg.get('path', '')
                                control['path_edit'].setText(self.format_path_display(full_path))
                                control['path_edit'].setToolTip(full_path)
            except Exception as e:
                print(f"Error loading dictionary settings: {str(e)}")

            #print("LOADING :",settings)

    def change_keyword_method(self, index):
        """Switch between keyword methods"""
        self.current_method = self.keyword_methods[index]
        self.method_stack.setCurrentIndex(index)
        


    def change_manual_profile(self, index):
        """Change manual keyword profile and save current content"""
        if hasattr(self, 'current_manual_profile'):
            current_text = self.keyword_input.toPlainText()
            self.manual_profiles[self.current_manual_profile] = [
                line.strip() for line in current_text.splitlines() if line.strip()
            ]
        
        profile_name = self.profile_dropdown.itemText(index)
        self.current_manual_profile = profile_name
        self.keyword_input.setPlainText("\n".join(self.manual_profiles[profile_name]))




    def get_unique_preset_name(self, base_name):
        """Generate a unique preset name by adding incremental number if needed"""
        name = base_name
        counter = 1
        while os.path.exists(os.path.join(self.text_presets_dir, name + ".txt")):
            name = f"{base_name} ({counter})"
            counter += 1
        return name

    def multi_select_files(self):
        """Select multiple files and generate name"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Supported Files (*.epub *.pdf *.txt)")
        
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            for file in files:
                if file and file not in self.selected_files:
                    self.selected_files.append(file)
                    display_path = self.format_path_display(file)
                    self.list_widget.addItem(display_path)
            
            self.update_preset_name()

    def remove_file(self):
        """Remove selected file from list"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        # Get the full paths of selected items by matching display names
        for item in selected_items:
            display_path = item.text()
            # Find the full path that matches this display path
            for file in self.selected_files[:]:  # Make a copy for iteration
                if self.format_path_display(file) == display_path:
                    self.selected_files.remove(file)
                    break
            self.list_widget.takeItem(self.list_widget.row(item))
        
        self.update_preset_name()

    def update_preset_name(self):
        """Update the preset name based on selected files"""
        if not self.selected_files:
            self.preset_name_edit.setText("")
            return
        
        first_file = os.path.splitext(os.path.basename(self.selected_files[0]))[0]
        if len(self.selected_files) == 1:
            base_name = f"TEXT_{first_file}"
        else:
            base_name = f"TEXT_{first_file} + ({len(self.selected_files)-1})"
        
        unique_name = self.get_unique_preset_name(base_name)
        self.preset_name_edit.setText(unique_name)



    def format_path_display(self, path):
        """Format path for display (show last 2 components)"""
        if not path:
            return ""
        parts = path.replace('\\', '/').split('/')
        if len(parts) > 2:
            return f".../{'/'.join(parts[-2:])}"
        return path


    def closeEvent(self, event):
        """Save settings when dialog is closed (including with Cancel)"""
        self.save_dictionary_settings()
        super().closeEvent(event)

    # And add this new method:
    def close_dialogue(self):
        """Handle cancel button click"""
        self.save_dictionary_settings()
        self.reject()  # This properly closes the dialog


    def get_selected_files(self):
        return self.selected_files

    def get_all_keyword_profiles(self):
        """Return all keyword profiles based on current method"""
        self.save_dictionary_settings()
        
        if self.current_method == self.keyword_methods[0]:  # Dictionary Presets
            profiles = {}
            for i, control in enumerate(self.dictionary_controls):
                if control['checkbox'].isChecked() and control['path_edit'].toolTip():
                    try:
                        with open(control['path_edit'].toolTip(), 'r', encoding='utf-8') as f:
                            keywords = [line.strip() for line in f.readlines() 
                                      if line.strip() and not line.strip().startswith(';')]
                            
                            if i == 0:  # Ignored keywords
                                profiles["Ignored keywords"] = keywords
                            else:
                                profiles[f"Highlight color {i}"] = keywords
                    except Exception as e:
                        print(f"Error loading dictionary file: {str(e)}")
            return profiles
        else:  # Manual Search
            current_text = self.keyword_input.toPlainText()
            self.manual_profiles[self.current_manual_profile] = [
                line.strip() for line in current_text.splitlines() if line.strip()
            ]
            
            profiles = {}
            for name in [f"Highlight color {i}" for i in range(1, 10)] + ["Ignored keywords"]:
                if name in self.manual_profiles:
                    if name == "Ignored keywords":
                        profiles[name] = self.manual_profiles[name]
                    else:
                        profiles[name] = self.manual_profiles[name]
                else:
                    profiles[name] = []
            return profiles



# Custom QTableWidget that enforces at least one selected row
class EnforcedSelectionTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_row = 0
        # Install event filter to catch mouse clicks
        self.viewport().installEventFilter(self)
        
    def selectionCommand(self, index, event):
        # This method gets called whenever selection is about to change
        # Get the current selection command
        command = super().selectionCommand(index, event)
        
        # If this would clear selection, adjust the command
        if command == QItemSelectionModel.Clear:
            # Store the last selected row
            selected_rows = self.selectionModel().selectedRows()
            if selected_rows:
                self.current_row = selected_rows[0].row()
            return QItemSelectionModel.NoUpdate
            
        return command
        
    def mousePressEvent(self, event):
        # Store the current selected row before handling the mouse press
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            self.current_row = selected_rows[0].row()
        
        # Let QTableWidget handle the mouse press
        super().mousePressEvent(event)
        
        # Ensure we still have a selection after the event
        if not self.selectionModel().selectedRows():
            # No row is selected, re-select the previous row
            self.selectRow(self.current_row)
            
    def mouseReleaseEvent(self, event):
        # Store the current selected row
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            self.current_row = selected_rows[0].row()
            
        # Let QTableWidget handle the mouse release
        super().mouseReleaseEvent(event)
        
        # Check if we have a selection after the event
        if not self.selectionModel().selectedRows():
            # No row is selected, re-select the previous row
            self.selectRow(self.current_row)
            
    def viewportEvent(self, event):
        # Additional protection for viewport events
        result = super().viewportEvent(event)
        
        # After any viewport event, check if we have a selection
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick):
            if not self.selectionModel().selectedRows():
                self.selectRow(self.current_row)
                
        return result


class LabelManagerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, labels_dict=None):
        super().__init__(parent)
        self.parent = parent
        self.labels_dict = labels_dict or {"Default": "#00000000"}
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Label Manager")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Label list
        self.label_list = EnforcedSelectionTable()  # Using custom table widget
        self.label_list.setColumnCount(2)
        self.label_list.setHorizontalHeaderLabels(["Label Name", "Color"])
        self.label_list.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.label_list.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.label_list.horizontalHeader().setFocusPolicy(Qt.NoFocus)
        self.label_list.setColumnWidth(1, 80)
        self.label_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.label_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_list.verticalHeader().setVisible(False)
        # Populate the list
        self.refresh_label_list()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Label")
        self.edit_button = QPushButton("Edit Label")
        self.delete_button = QPushButton("Delete Label")
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        
        # Connect signals
        self.add_button.clicked.connect(self.add_label)
        self.edit_button.clicked.connect(self.edit_label)
        self.delete_button.clicked.connect(self.delete_label)
        # Add selection change handler to control the delete button state
        self.label_list.itemSelectionChanged.connect(self.update_button_states)
            
        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(self.ok_button)
        
        self.ok_button.clicked.connect(self.accept)
        
        # Add everything to main layout
        layout.addWidget(self.label_list)
        layout.addLayout(buttons_layout)
        layout.addLayout(dialog_buttons)
        
        self.setLayout(layout)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        color_delegate = LabelColorDelegate(self.label_list)
        self.label_list.setItemDelegateForColumn(1, color_delegate)
        
        # Select the first row by default
        self.label_list.selectRow(0)
        # Initially update button states based on the first row selection
        self.update_button_states()
        self.init_message_boxes()

    def update_button_states(self):
        """Update button states based on current selection"""
        current_row = self.label_list.currentRow()
        if current_row >= 0:
            current_name = self.label_list.item(current_row, 0).text()
            # Disable delete button if "Default" is selected
            self.delete_button.setEnabled(current_name != "Default")
        else:
            # If nothing is selected, disable delete button
            self.delete_button.setEnabled(False)

    def init_message_boxes(self):
        """Initialize custom message box settings."""
        self.message_box = QtWidgets.QMessageBox(self)
        self.message_box.setIcon(QtWidgets.QMessageBox.NoIcon)  # Set to no icon by default
    
    def show_info_message(self, title, message):
        """Show an information message box without an icon."""
        self.message_box.setWindowTitle(title)
        self.message_box.setText(message)
        self.message_box.exec_()



    def refresh_label_list(self):
        self.label_list.setRowCount(0)
        
        for name, color in self.labels_dict.items():
            row = self.label_list.rowCount()
            self.label_list.insertRow(row)
            
            # Label name
            name_item = QTableWidgetItem(name)
            self.label_list.setItem(row, 0, name_item)
            
            # Color swatch
            color_item = QTableWidgetItem("")
            color_item.setBackground(QColor(color))
            self.label_list.setItem(row, 1, color_item)
    
    def add_label(self):
        name, ok = QInputDialog.getText(self, "New Label", "Enter label name:")
        if ok and name:
            if name in self.labels_dict:
                self.show_info_message('Duplicate', "Label name already exists.")
                return
            
            color = QColorDialog.getColor()
            if color.isValid():
                self.labels_dict[name] = color.name()
                self.refresh_label_list()
    
    def edit_label(self):
        current_row = self.label_list.currentRow()
        if current_row < 0:
            self.show_info_message("No Selection", "Please select a label to edit.")
            return
        
        current_name = self.label_list.item(current_row, 0).text()
        
        # Don't allow editing the Default label
        if current_name == "Default":
            color = QColorDialog.getColor(QColor(self.labels_dict["Default"]))
            if color.isValid():
                self.labels_dict["Default"] = color.name()
                self.refresh_label_list()
                print("Color Updated", "Default label color has been updated.")
            return
        
        new_name, ok = QInputDialog.getText(self, "Edit Label", "Enter new label name:", text=current_name)
        if ok and new_name:
            if new_name != current_name and new_name in self.labels_dict:
                self.show_info_message("Duplicate", "Label name already exists.")
                return
            
            color = QColorDialog.getColor(QColor(self.labels_dict[current_name]))
            if color.isValid():
                # If name changed, we need to update any presets using this label
                if new_name != current_name:
                    # Store the color value
                    color_value = self.labels_dict[current_name]
                    # Delete the old key
                    del self.labels_dict[current_name]
                    # Create new key with same color
                    self.labels_dict[new_name] = color_value
                    
                    # Update preset assignments
                    if hasattr(self.parent, 'preset_labels_dictionary'):
                        for preset, label in self.parent.preset_labels_dictionary.items():
                            if label == current_name:
                                self.parent.preset_labels_dictionary[preset] = new_name
                
                # Update the color value
                self.labels_dict[new_name] = color.name()
                self.refresh_label_list()
    
    def delete_label(self):
        current_row = self.label_list.currentRow()
        if current_row < 0:
            self.show_info_message("No Selection", "Please select a label to delete.")
            return
        
        current_name = self.label_list.item(current_row, 0).text()
        
        # Don't allow deleting the Default label
        if current_name == "Default":
            self.show_info_message("Reserved", "Cannot delete the Default label.")
            return
        

        # Remove the label
        del self.labels_dict[current_name]
        
        # Reassign any presets using this label to Default
        if hasattr(self.parent, 'preset_labels_dictionary'):
            for preset, label in self.parent.preset_labels_dictionary.items():
                if label == current_name:
                    self.parent.preset_labels_dictionary[preset] = "Default"
        
        self.refresh_label_list()
            
    def get_labels(self):
        return self.labels_dict



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
    

    parser = argparse.ArgumentParser(description="Sentence Queuer Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for "create_preset"
    create_preset_parser = subparsers.add_parser("create_preset", help="Process text folder")
    create_preset_parser.add_argument("-selected_files", required=True, nargs="+", help="List of file paths of text files to process")
    create_preset_parser.add_argument("-keyword_profiles", required=True, type=json.loads, help="Profiles in JSON format")
    create_preset_parser.add_argument("-preset_name", default="preset_output", help="Name of the preset")
    create_preset_parser.add_argument("-highlight_keywords", type=lambda x: x.lower() == "true", default=True, help="Highlight keywords (True/False)")
    create_preset_parser.add_argument("-output_option", default="Single output", help="Output option")
    create_preset_parser.add_argument("-get_metadata", type=lambda x: x.lower() == "true", default=True, help="Extract metadata (True/False)")
    create_preset_parser.add_argument("-max_length", type=int, default=200, help="Maximum sentence length")
    create_preset_parser.add_argument("-output_folder", help="Folder to save the preset file. Defaults to text_presets_dir if not provided.")

    # Subparser for "start_session_from_files"
    session_parser = subparsers.add_parser("start_session_from_files", help="Start session from files")
    session_parser.add_argument("-sentence_preset_path", required=True, help="Path to the sentence preset file")
    session_parser.add_argument("-session_preset_path", required=True, help="Path to the session preset file")
    session_parser.add_argument("-randomize_settings", type=lambda x: x.lower() == "true", default=True, help="Randomize settings (True/False)")
    session_parser.add_argument("-autocopy_settings", type=lambda x: x.lower() == "true", default=False, help="Clipboard settings (True/False)")



    # Parse arguments
    args = parser.parse_args()

    if args.command == "create_preset":
        app = QtWidgets.QApplication(sys.argv)
        view = MainApp(show_main_window=False)
        view.create_preset(
            selected_files=args.selected_files,
            keyword_profiles=args.keyword_profiles,
            preset_name=args.preset_name,
            highlight_keywords=args.highlight_keywords,
            output_option=args.output_option,
            max_length=args.max_length,
            metadata_settings=args.get_metadata,
            output_folder=args.output_folder,
            is_gui=False
        )
        app.quit()

    elif args.command == "start_session_from_files":
        app = QtWidgets.QApplication(sys.argv)
        view = MainApp(show_main_window=False)
        view.start_session_from_files(
            sentence_preset_path=args.sentence_preset_path,
            session_preset_path=args.session_preset_path,
            randomize_settings=args.randomize_settings,
            autocopy_settings=args.autocopy_settings,
        )
        sys.exit(app.exec_())


    else:
        app = QtWidgets.QApplication(sys.argv)
        # Default behavior: Start the GUI
        view = MainApp(show_main_window=True)
        sys.exit(app.exec_())




