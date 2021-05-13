# dragonfly-commands

This repository contains speech commands and macros for the following programs and languages:
- Visual Studio: C#
- WebStorm: HTML, CSS, JavaScript, React
- Sublime Text
- SourceTree
- Slack
- Chrome
- Windows Explorer
- Outlook 

For demonstration videos, visit my channel on YouTube: [VoiceProgrammer](https://www.youtube.com/channel/UCaGFoHSOdtybMJJN7EATsBg)  

It requires the speech recognition software Dragon NaturallySpeaking (DNS). Due to a file loading issue, most of the commands are defined in the file `_commands.py`. If new commands are placed in this file, DNS will pick them up immediately after mic is turned off/on. The command modules are work in progress so changes will occur. 

Based on code written by wolfmanstout [dragonfly-commands](https://github.com/wolfmanstout/dragonfly-commands).

## Setup
- Dragonfly installation
 - Install the prerequisites for dragonfly: http://dragonfly.readthedocs.io/en/latest/installation.html
 - Download  dragonfly from: https://github.com/t4ngo/dragonfly
 - Navigate to the downloaded dragonfly directory in Command Prompt and run `python setup.py install`.
- Find your python directory. Go to file "C:\Python27\Lib\site-packages\dragonfly-0.6.6b1-py2.7.egg\dragonfly\__init__.py". In line 37, add `RuleWrap` to the list of imports.
- Clone this repository.
- Open "Configure NatLink via GUI". Click "Enable" under UserDirectory, and find the folder with this repository.
- Open Dragon NaturallySpeaking, a box with the title "Messages from NatLink" should pop up.
- In Dragon, under "Now listening for...", choose "Commands".

Note that NatLink must be opened before the Dragon software. 

My setup:
- Windows 8.1 x64
- ActivePython-2.7.10.12-win32-x86
- wxPython3.0-win32-3.0.2.0-py27
- natlink-4.1papa
- Dragonfly
- Dragon Professional 14
