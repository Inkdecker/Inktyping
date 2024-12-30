<p align="center">
  <img src="https://github.com/Inkdecker/session_writing/blob/main/ui/resources/icons/sample.png" alt="Project Screenshot" width="600"/>
</p>

# <img src="https://raw.githubusercontent.com/Inkdecker/session_writing/refs/heads/main/ui/resources/icons/session_writing.png" width="25" style="vertical-align: middle;" /> Session Writing

This is a free text mining tool users can use to extract, highlight and display multiples sentences from text files using a list of keywords and prefixes.

It can be used to either analyze text for research purposes or practice writing.

# Features
	- Sentence extraction using multiple keywords
	- Handling of both singular and plural forms
	- Ability to select keywords to ignore
	- Up to 9 different color profiles for the highliting of the keywords
   	- Ability to customize themes, highlight colors and shortcuts
	- Autocopy sentences to clipboard
	- Rich text / Plain text copy

	- 04.12.2014: Ability to create Rainmeter profiles to export the slideshows
	
   	- (New) 30.12.2014 New: Main functions available from commande line and metadata extraction
    
##### Supported files :  .txt, .epub, .pdf


# Usage
[Download](https://github.com/Inkdecker/session_writing/releases/download/1.0/session_writing.exe) and run the executable, no installation needed.

1 - Click **"Add Folders"**, then select 1 or more folders containing the text files **(.txt, .epubs or .pdf)** you wish to process.

> Note : You can drag your favorite folders to the left column of the explorer to pin them for a quick access.

2 - Enter the **keywords** you want to use to extract the sentences, you can also use **keywords** to ignore. The program will by default add or remove the letter [s] at the end of the given Keyword to create and search an additional form of the word. 

> [House] --> [House] & [Houses], [Cars] --> [Car] & [Cars], etc...


Prefix | Result
------------ | -------------
**Keyword** | search for both singular and plural forms [Keyword and Keywords]
**&Keyword** | search the given form [Keyword]
**Keyword1 + Keyword2 + ...** | search for multiple keywords in a sentence, either forms
**&Keyword1 + &Keyword2 + ...** | search for multiple keywords in a sentence, given forms
**!Keyword** | ignore sentences with either singular or plural forms [ignore Keyword and Keywords]
**!&Keyword** | ignore sentences with the given form [ignore Keyword]
**#Keyword** | highlight the given form without searching it
**;Comment** | ignore line 


3 - Check **"Highlight Keywords"** if you want your keywords to be highlighted in output files for later processing. Check **"Extract Metadata"** to add the following information to the sentences when available [Title, Author, Date].

4 - Select **"Single output"** to store all the sentences into a single files, **"All output"** to produce additional files for each individual keywords.

5 - Click "OK", the extracted sentences will be stored inside the **"../text_preset/"** folder, the sentences separated by an empty line.

6 - Create or select a preset with the settings that you want to use for the session.

7 - Click "Start" to begin the session.

> Note: You can select "Randomize" to shuffle the pictures and "Start session" to automatically start the session whenever the program is launched using your latest settings.
> 
> Note: You can select "Clipboard" to automatically copy the sentences to the clipboard.

## Rainmeter
The sentence preset can be exported and used as rainmeter slideshow. To do so, select the sentence preset you want to export and press the [Rainmeter] button. You can then place the created profile inside your **"..\RAINMETER\Skins"** folder and then launch it using rainmeter.
> Note: The TEXT_SLIDESHOW.ini file can be edited to customise the slideshow. Most variables can be found in the [Variables] section.
> 
> Note: Deleted sentences get stored inside a new text file send to the "..\rainmeter_presets\Deleted Files" folder. 

## Command line
### Create preset
- **create_preset**
  - **`-folder_list` (required)**: Path(s) to the folder(s) containing text files
  - **`-keyword_profiles` (required)**: Profiles in JSON format
  - **`-preset_name` (optional)**: Name of the preset |  *Default*: `"preset_output"`
  - **`-highlight_keywords` (optional)**: Highlight keywords (`True`/`False`) | *Default*: `True`
  - **`-output_option` (optional)**: Output option (`"Single output"`/`"All output"`) |  *Default*: `"Single output"`
  - **`-max_length` (optional)**: Maximum sentence length (in characters) |  *Default*: `200`
  - **`-get_metadata` (optional)**: Extract metadata (`True`/`False`) |  *Default*: `True`
  - **`-output_folder` (optional)**: Folder to save the preset file
 
##### Example :
```batch
session_writing.exe create_preset -folder_list "D:\Desktop\Book_Folder_1" "D:\Desktop\Book_Folder_2" -keyword_profiles "{\"Highlight color 1\": [\"keyword1\",\"keyword2\",\"keyword3\"], \"Highlight color 2\": [,\"keyword4\"]}" -preset_name "Text_preset_1" -get_metadata True -highlight_keywords True -output_folder "D:\Desktop\Output_Folder"
```
### Start session
- **start_session_from_files**
  - **`-sentence_preset_path` (required)**: Path to the sentence preset file
  - **`-session_preset_path` (required)**: Path to the session preset file
  - **`-randomize_settings` (optional)**: Randomize settings (`True`/`False`)  |  *Default*: `True`
  - **`-clipboard_settings` (optional)**: Clipboard keywords (`True`/`False`) | *Default*: `False`
 
##### Example :
```batch
session_writing.exe start_session_from_files -sentence_preset_path "D:\Desktop\preset_1.txt" -session_preset_path "D:\Desktop\session_presets_1.txt" -randomize_settings True -clipboard_settings False
```

## Troubleshooting 
- Delete the **session_settings.txt** to reset settings and shortcuts.
- Delete the **preset** folder and restart the executable to reset everything back to default.
- Default encoding is **UTF-8** so the presets files should be encoded as such.

## Hotkeys
All **hotkeys** can be modified through the **session_settings.txt** inside the preset folder, however, be careful as <ins>duplicate the keys get disabled</ins>.

### Configuration window:
Button | Hotkey
------------ | -------------
Start session | S
Close Window | Escape

### Session Window: 
Button | Hotkey
------------ | -------------
Zoom + | Q, Numpad +, Mousewheel
Zoom - | D, Numpad -, Mousewheel
Toggle highlight | G
Toggle text field | T
Open color window | F1
Toggle Always On Top | A
Previous sentence | Left Arrow Key, Shift + Backspace
Stop | Esc 
Pause | Spacebar
Next sentence | Right Arrow Key, Return
Copy sentence [Plain text] | C
Copy sentence [Rich text] | Ctrl + C
Toggle autocopy to clipboard | Shift + C
Open preset folder | O
Delete sentence | Ctrl + D
Open setting window | Tab
Add 30s | Up Arrow Key
Add 1 Minute | Ctrl + Up Arrow Key
Reset timer | Ctrl + Shift + Up Arrow Key

### Rainmeter Slideshow: 
Button | Hotkey
------------ | -------------
Previous Sentence | Left click
Next Sentence | Right click
Open Text File | Middle click
Copy Text File Path | Scroll up
Close slideshow | Scroll down
Move image to "..\rainmeter_presets\Deleted Files" | Mouse button 1
Open Sentence folder | Mouse button 2

## Licence
[GNU General Public License v3.0](https://github.com/Inkdecker/session_writing/blob/main/LICENSE)
