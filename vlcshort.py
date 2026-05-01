import keyboard
import requests

VLC_PASSWORD = "vlc"  # change to whatever you set
VLC_URL = "http://localhost:8080/requests/status.xml"

def next_track():
    requests.get(VLC_URL, params={"command": "pl_next"}, auth=("", VLC_PASSWORD))

keyboard.add_hotkey("F4+num 6", next_track, suppress=True)
keyboard.wait()