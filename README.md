<div align="center">
  <table>
    <tr>
      <td><img src="https://github.com/Inkdecker/Inktyping/blob/main/ui/resources/icons/sample%20(1).png" alt="Screenshot 1" width="300"/></td>
      <td><img src="https://github.com/Inkdecker/Inktyping/blob/main/ui/resources/icons/sample%20(2).png" alt="Screenshot 2" width="300"/></td>
    </tr>
    <tr>
      <td><img src="https://github.com/Inkdecker/Inktyping/blob/main/ui/resources/icons/sample%20(3).png" alt="Screenshot 3" width="300"/></td>
      <td><img src="https://github.com/Inkdecker/Inktyping/blob/main/ui/resources/icons/sample%20(4).png" alt="Screenshot 4" width="300"/></td>
    </tr>
  </table>
</div>


# <img src="https://raw.githubusercontent.com/Inkdecker/Inktyping/refs/heads/main/ui/resources/icons/Inktyping.png" width="25" style="vertical-align: middle;" /> Inktyping

This is a free toll for text exploration that users can use to extract, highlight and display multiples sentences from text files using a list of keywords and prefixes.

It can be used to either analyze text for research purposes or practice writing.

# Features
	- Sentence extraction using multiple keywords
	- Handling of both singular and plural forms
	- Ability to select keywords to ignore
	- Up to 9 different color profiles for the highliting of the keywords
	- Ability to customize themes, highlight colors and shortcuts
	- Autocopy sentences to clipboard
	- Rich text / Plain text copy
	
	- 04.12.2024: Ability to create Rainmeter profiles to export the slideshows
	- 30.12.2024: Main functions available from commande line and metadata extraction
	- 28.03.2025: Search function for the sentence presets.
	- 31.03.2025: Added the use of keyword dictionaries as a new parsing method
	- 07.04.2025: Added color labels to the sentence preset table.
 
	- (New) 18.04.2025: Renamed from session_drawing to Inktyping.
##### Supported files :  .txt, .epub, .pdf


# Usage
[Download](https://github.com/Inkdecker/Inktyping/releases/latest/download/Inktyping.exe) and run the executable, no installation needed.

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
  - **`-selected_files` (required)**: List of file paths of text files to process
  - **`-keyword_profiles` (required)**: Profiles in JSON format `{'Ignored keywords': [], 'Highlight color 1': [], 'Highlight color 2': [], 'Highlight color 3': [], 'Highlight color 4': [], 'Highlight color 5': [], 'Highlight color 6': [], 'Highlight color 7': [], 'Highlight color 8': [], 'Highlight color 9': []}`
  - **`-preset_name` (optional)**: Name of the preset |  *Default*: `"preset_output"`
  - **`-highlight_keywords` (optional)**: Highlight keywords (`True`/`False`) | *Default*: `True`
  - **`-output_option` (optional)**: Output option (`"Single output"`/`"All output"`) |  *Default*: `"Single output"`
  - **`-max_length` (optional)**: Maximum sentence length (in characters) |  *Default*: `200`
  - **`-get_metadata` (optional)**: Extract metadata (`True`/`False`) |  *Default*: `True`
  - **`-output_folder` (optional)**: Folder to save the preset file
 
##### Example :
```batch
Inktyping.exe create_preset -selected_files "D:\Desktop\Book1.epub" "D:\Desktop\Book2.epub" -keyword_profiles "{\"Ignored keywords\": [\"Ignored_keyword_1\",\"Ignored_keyword_2\"], \"Highlight color 1\": [\"keyword1\",\"keyword2\",\"keyword3\"], \"Highlight color 2\": [\"keyword4\"]}" -preset_name "Text_preset_1" -get_metadata True -highlight_keywords True -output_folder "D:\Desktop\Output_Folder"
```
### Start session
- **start_session_from_files**
  - **`-sentence_preset_path` (required)**: Path to the sentence preset file
  - **`-session_preset_path` (required)**: Path to the session preset file
  - **`-randomize_settings` (optional)**: Randomize settings (`True`/`False`)  |  *Default*: `True`
  - **`-clipboard_settings` (optional)**: Clipboard keywords (`True`/`False`) | *Default*: `False`
 
##### Example :
```batch
Inktyping.exe start_session_from_files -sentence_preset_path "D:\Desktop\preset_1.txt" -session_preset_path "D:\Desktop\session_presets_1.txt" -randomize_settings True -clipboard_settings False
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
Cycle labels | ²
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
[GNU General Public License v3.0](https://github.com/Inkdecker/Inktyping/blob/main/LICENSE)
