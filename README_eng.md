# Alcatel OXE Subscriber Name Update Script

This script automates updating a subscriber's first and last name on an **Alcatel OXE** PBX via Telnet.  
It features a graphical interface (Tkinter), performs Cyrillic-to-Latin transliteration, and sends commands to the PBX management console.

## Python Requirements

- Python version: **3.9 – 3.13** (inclusive)
- Tested on Python 3.12.9
- Note: In Python 3.13, the `telnetlib` module is still available but may be removed in future versions. If needed, it can be replaced with `telnetlib3` (not required for the current version).

**Standard libraries:** All used modules are part of the Python standard library, except `tkinter`, which may require a separate installation on some systems.

## Installation and Environment Setup

1. Install **Python 3.9–3.13** from the official python.org website.  
   During installation on Windows, ensure the *"Add Python to PATH"* option is checked.

2. Install `tkinter` (if not already installed):
   - **Windows / macOS**: `tkinter` is included in the standard distribution; no extra steps needed.
   - **Linux (Debian/Ubuntu)**:
     ```bash
     sudo apt update
     sudo apt install python3-tk
Linux (Red Hat/Fedora):

bash
sudo dnf install python3-tkinter
Verify that all required modules are available. No additional third‑party libraries are required.

Configuration
1. servers.json File
The script uses a servers.json file to map region codes to PBX IP addresses and the mtcl account password.

Default file path:
C:\alcatel_script\servers\servers.json
(This path can be changed in the Config class.)

File structure:

json
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
region_code – two‑digit region code (the first two digits after the leading 9 in the subscriber number).

address – PBX IP address.

mtcl – password for the mtcl account (the username is fixed as mtcl).

Important:
Ensure that every region code appearing in subscriber numbers has a corresponding entry in this file.
The script will throw an error if a region code mapping is missing.

2. Logging
Logs are written to C:\alcatel_script\changes.log (the path is configurable via Config.LOG_FILE).
The directory is created automatically on the first run.

3. Subscriber Number Format
The script expects numbers in the format 9xxyyyy, where:

xx – region code (2 digits),

yyyy – remaining 4 digits.

The PBX IP address is determined by the region code xx from servers.json.

Usage
Open a command prompt (terminal).

Navigate to the folder containing the script.

Run the script:

bash
python change_FIO3.0.py
A graphical window will appear:

Enter the subscriber number (e.g., 9011666).

The corresponding PBX IP address will be displayed automatically (from servers.json).

Enter the last name and first name in Cyrillic.

Click "Rename" (or the corresponding button).

A success or error message will be shown after the operation completes.

Code Structure (for Developers)
Config – stores settings (paths, timeouts, constants).

Transliterator – handles Cyrillic‑to‑Latin transliteration.

ServerManager – reads servers.json and provides IP and password by region code.

AlcatelSession – low‑level Telnet communication.

AlcatelOXEClient – executes mgr scripts on the PBX.

SubscriberUpdater – core business logic for updating a subscriber.

GUI – Tkinter graphical interface.
