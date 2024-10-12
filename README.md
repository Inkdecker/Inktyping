<p align="center">
  <img src="https://github.com/Inkdecker/session_writing/blob/main/ui/resources/icons/sample.png" alt="Project Screenshot" width="600"/>
</p>

# Session_writing

This is a free text mining tool users can use to extract, highlight and display multiples sentences from text files using a list of keywords and prefixes.

It can be used to either analyze text for research purposes or practice writing.

# Features
	- Sentence extraction using multiple keywords
	- Handling of both singular and plural forms
	- Ability to select keywords to ignore
	- 2 types of highlighting for both Names and Keywords
    - Ability to customize themes, highlight colors and shortcuts
##### Supported files :  .txt, .epubs, .pdf


# Usage
[Download](https://github.com/Inkdecker/session_writing/releases/download/1.0/session_writing.exe) and run the executable, no installation needed.

1 - Click **"Add Folders"**, then select 1 or more folders containing the text files **(.txt, .epubs or .pdf)** you wish to process.

2 - Enter the **keywords** you want to use to extract the sentences, you can also use **keywords** to ignore.

Prefix | Result
------------ | -------------
**Keyword** | search for both singular and plural forms
**&Keyword** | search the given form
**!Keyword** | ignore sentences with either singular or plural forms
**!&Keyword** | ignore sentences with the given form

3 - Check **"Highlight Keywords"** if you want your keywords to be highlighted in output files for later processing. 

4 - Select **"Single output"** to store all the sentences into a single files, **"All output"** to produce additional files for each individual keywords.

5 - Click "OK", the extracted sentences will be stored inside the **text_preset/** folder, the sentences separated by an empty line.

## Troubleshooting 
- Delete the **session_settings.txt** to reset settings and shortcuts.
- Delete the **preset** folder and restart the executable to reset everything back to default.
- Default encoding is **UTF-8** so the presets files should be encoded as such.

## Hotkeys
All **hotkeys** can be modified through the **session_settings.txt** inside the preset folder, however, be careful as <u>duplicate the keys get disabled</u>.

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
Toggle Always On Top | A
Previous sentence | Left Arrow Key
Stop | Esc 
Pause | Spacebar
Next sentence | Right Arrow Key, Return
Copy sentence | C
Open preset folder | O
Delete sentence | Ctrl + D
Open setting window | Tab
Add 30s | Up Arrow Key
Add 1 Minute | Ctrl + Up Arrow Key
Reset timer | Ctrl + Shift + Up Arrow Key
