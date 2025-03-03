################################################
########## RICH TEXT COPY ARG ##################
################################################

from PyQt5 import QtCore, QtWidgets
import sys
import argparse
import re
from html import escape
from PyQt5.QtWidgets import QApplication

def parse_color_data(color_string):
    """Parses the color data and returns a dictionary."""
    color_dict = {}
    
    text_color_match = re.search(r'Text_color:(\d+),\s*(\d+),\s*(\d+),\s*255', color_string)
    if text_color_match:
        r, g, b = text_color_match.groups()
        color_dict['text_color'] = f'rgb({r}, {g}, {b})'
    else:
        raise ValueError("Text_color not found in input")

    color_matches = re.findall(r'Color(\d+):(\d+),(\d+),(\d+)', color_string)
    for num, r, g, b in color_matches:
        color_dict[f'Color{num}'] = f'rgb({r}, {g}, {b})'

    return color_dict

def apply_rich_text(sentence, color_dict):
    """Applies rich text formatting to the sentence."""
    
    def replace_with_color(match):
        curly_count = len(match.group(1))
        keyword = match.group(2)
        color_key = f'Color{curly_count}'
        color = color_dict.get(color_key, color_dict.get('Color1', 'rgb(255,255,255)'))
        return f'<span style="color: {color}">{escape(keyword)}</span>'
    
    # Apply keyword highlights
    highlighted_sentence = re.sub(r'(\{+)([^{}]+)(\}+)', replace_with_color, sentence)
    
    # Apply overall text color and add two line breaks using both <br> and <p> tags
    # We wrap the content in a <div> to ensure proper spacing
    highlighted_sentence = f'''
    <div style="white-space: pre-wrap;">
        <span style="color: {color_dict["text_color"]}">{highlighted_sentence}</span>
        <p>&nbsp;</p>
        <p>&nbsp;</p>
    </div>
    '''
    return highlighted_sentence

def copy_to_clipboard(html_text, plain_text):
    """Copies both HTML and plain text to the clipboard."""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        clipboard = QApplication.clipboard()
        mime_data = QtCore.QMimeData()
        
        # Ensure proper HTML document structure
        full_html = f'''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html>
            <head>
                <meta charset="utf-8">
            </head>
            <body>
                {html_text}
            </body>
        </html>
        '''
        
        mime_data.setData('text/html', full_html.encode('utf-8'))
        # Add two actual linebreaks to the plain text
        # Using \r\n for better Windows compatibility
        mime_data.setText(plain_text + '\r\n\r\n')
        clipboard.setMimeData(mime_data)
        print(f"Copied Rich Text (HTML): {html_text}")
        
    except Exception as e:
        print("Error copying HTML to clipboard:", e)
        
def rich_text_copy(filepath):
    """Copies both HTML and plain text to the clipboard."""
    try:
        # Read from the temporary file
        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read().strip()
        # Process the data
        sentence, color_data = data.split("||")
        color_dict = parse_color_data(color_data)
        rich_text = apply_rich_text(sentence, color_dict)
        # Remove curly brackets for plain text and ensure proper line endings
        plain_text = re.sub(r'\{+([^{}]+)\}+', r'\1', sentence)
        copy_to_clipboard(rich_text, plain_text)
        
    except Exception as e:
        print("Error processing input:", e)
        




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Sentence Queuer Tool")
    subparsers = parser.add_subparsers(dest="command")


    # Subparser for "start_session_from_files"
    rich_text_copy_parser = subparsers.add_parser("rich_text_copy", help="Convert tempfile informations into rich text and store it into the clipboard")
    rich_text_copy_parser.add_argument("-temp_file_path", required=True, help="Path to the sentence temp file")


    # Parse arguments
    args = parser.parse_args()



    if args.command == "rich_text_copy":
        rich_text_copy(filepath=args.temp_file_path,)
        




