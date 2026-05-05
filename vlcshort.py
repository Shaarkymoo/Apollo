import keyboard
import requests
import ctypes

VLC_PASSWORD = "vlc"  # change to whatever you set
VLC_URL = "http://localhost:22123/requests/status.xml"

def next_track():
    requests.get(VLC_URL, params={"command": "pl_next"}, auth=("", VLC_PASSWORD))

def prev_track():
    requests.get(VLC_URL, params={"command": "pl_previous"}, auth=("", VLC_PASSWORD))

def seek_forward():
    requests.get(VLC_URL, params={"command": "seek", "val": "+10S"}, auth=("", VLC_PASSWORD))

def seek_backward():
    requests.get(VLC_URL, params={"command": "seek", "val": "-10S"}, auth=("", VLC_PASSWORD))

def play_pause():
    requests.get(VLC_URL, params={"command": "pl_pause"}, auth=("", VLC_PASSWORD))

def toggle_random():
    requests.get(VLC_URL, params={"command": "pl_random"}, auth=("", VLC_PASSWORD))

def close_window():
    ctypes.windll.user32.PostMessageW(
        ctypes.windll.user32.GetForegroundWindow(), 
        0x0010, 0, 0  # WM_CLOSE message
    )

# def next_track():
#     requests.get(VLC_URL, params={"command": "pl_next"}, auth=("", VLC_PASSWORD))

# def next_track():
#     requests.get(VLC_URL, params={"command": "pl_next"}, auth=("", VLC_PASSWORD))

# def next_track():
#     requests.get(VLC_URL, params={"command": "pl_next"}, auth=("", VLC_PASSWORD))

keyboard.block_key("F4")  # block F4 to prevent conflicts
keyboard.add_hotkey("alt+F4", close_window, suppress=True)
keyboard.add_hotkey("F4+num 9", next_track, suppress=True)
keyboard.add_hotkey("F4+num 8", toggle_random, suppress=True)
keyboard.add_hotkey("F4+num 7", prev_track, suppress=True)
keyboard.add_hotkey("F4+num 6", seek_forward, suppress=True)
keyboard.add_hotkey("F4+num 5", play_pause, suppress=True)
keyboard.add_hotkey("F4+num 4", seek_backward, suppress=True)
keyboard.wait()