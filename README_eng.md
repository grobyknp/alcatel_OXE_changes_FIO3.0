# alcatel_OXE_changes_FIO3.0
# Alcatel OXE PBX Subscriber Update Script

# Alcatel OXE Subscriber Updater

Script for automatic update of the name and surname of the subscriber on the Alcatel OXE PBX via Telnet.
It has a graphical interface (Tkinter), transliterates from Cyrillic to Latin and sends commands to the PBX management console.

---

## Python requirements

- Python version: 3.9 - 3.13 (inclusive)
- Tested on: Python 3.12.9
- Note: in Python 3.13, the telnetlib module is still available, but may be removed in future versions. If necessary, you can replace it with telnetlib3 (not required for the current version).
- Standard libraries: all modules are included in the standard Python delivery, except for tkinter (requires separate installation on some systems).

---

## Set up and configure the environment

1. install Python 3.9-3.13 from the official website python.org.
   On Windows, be sure to check the "Add Python to PATH" option.

2. setting tkinter (if not installed):

   - Windows/macOS: tkinter is included in the standard build.
   - Linux (Debian/Ubuntu):
sudo apt update
sudo apt install python3-tk

- Linux (Red Hat/Fedora):
sudo dnf install python3-tkinter


3. No additional libraries are required.

---

## Configuration

### Файл servers.json

The script uses the servers.json file to store the match:
region code -> PBX IP address and password for mtcl account.

The default path is C :\alcatel _ script\servers\servers.json (can be changed in the Config class).

#### File structure:

```json
[
{
"region_code": "01",
"address": "192.168.1.1",
"mtcl": "password_for_mtcl"
},
{
"region_code": "02",
"address": "192.168.2.1",
"mtcl": "another_password"
}
]
```
## Variable Description
region _ code two digits of the region code (first two digits after 9 in the number)
address IP address of the PBX
mtcl password for mtcl account (login is fixed)

For each region that appears in the numbers, there must be an entry in the file.

If there is no entry, the script will generate an error.

## Logging
Logs are written to the file:
C:\alcatel_script\changes.log (путь настраивается в Config.LOG_FILE).
The directory is created automatically the first time you start it.

Subscriber number format
The script expects a number in the format: 9xxyyyy

xx - region code (2 digits)

yyyy - remaining 4 digits

The IP address of the PBX is determined by the region code xx from servers.json.

## Launch
Open the command line (terminal).

Navigate to the script folder.

Execute the command:

python change_FIO3.0.py
The graphics window opens:

1) Enter the subscriber number (for example, 9011666).

The IP address of the PBX (from servers.json) is automatically displayed.

2) Enter last name and first name in Cyrillic.

3) Click Rename.

After execution, a success or error message appears.

## Description of classes
Config - storing settings (paths, timeouts, constants)

Translator - transliteration of Cyrillic into Latin

ServerManager - reading servers.json, obtaining IP and password by region code

AlcatelSession - low-level Telnet operation

AlcatelOXEClient - executing mgr scripts on the PBX

SubscriberUpdater - Basic Subscriber Update Business Logic

GUI - Tkinter interface
