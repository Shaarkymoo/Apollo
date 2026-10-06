# F4+Numpad VLC Shortcuts — Linux Design

## Purpose

Port the Windows `vlcshort.py` script to Pop OS (Linux, Wayland) with 6 global hotkeys that control VLC via its HTTP interface, without interfering with normal keyboard use or Alt+F4.

## Hotkeys (all use F4 as a layer modifier)

| Combo | VLC Command | HTTP Call |
|-------|-------------|-----------|
| F4 + Num9 | Next track | `command=pl_next` |
| F4 + Num8 | Toggle random | `command=pl_random` |
| F4 + Num7 | Previous track | `command=pl_previous` |
| F4 + Num6 | Seek forward +10s | `command=seek&val=+10S` |
| F4 + Num5 | Play/Pause toggle | `command=pl_pause` |
| F4 + Num4 | Seek backward -10s | `command=seek&val=-10S` |

## Key behavior

- **F4 + numpad [4-9]:** Keys are consumed (don't reach the focused app). VLC command is sent.
- **F4 alone (tap and release):** Forwarded normally to system. Alt+F4 still works.
- **F4 + any non-numpad key:** Both keys forwarded normally. F4 acts as a pass-through.
- **Numpad keys without F4:** Type normally. Unaffected.
- **VLC closed/reachable test**: Check HTTP endpoint; if unreachable, release grab and go idle.

## Architecture

### Components

1. **Background daemon script** (`vlcshort.py`)
   - Runs continuously, auto-started via XDG autostart
   - Polls VLC HTTP endpoint every 5 seconds for availability
   - When VLC is detected: grab the real keyboard exclusively (EVIOCGRAB)
   - Create a virtual uinput keyboard device for event forwarding
   - Enter event loop: read from real keyboard, forward to uinput unless F4+numpad combo matched
   - When VLC disappears: release grab, close uinput, go idle
   - Uses `signal` for clean shutdown

2. **XDG autostart** (`~/.config/autostart/vlc-shortcuts.desktop`)
   - `Type=Application`, `Exec=python3 /path/to/vlcshort.py`, `X-GNOME-Autostart-enabled=true`
   - Launches on login, runs in background

### Dependencies

- `python3-evdev` — read/write Linux input events, uinput for forwarding
- `python3-requests` — VLC HTTP API calls

### Permissions

- User must be in `input` group for evdev access
- `uinput` kernel module must be loaded (typically default on Pop OS)

## Flow

```
┌──────────────────────────────────────────────────┐
│  vlcshort.py (daemon)                            │
│                                                  │
│  ┌──────────┐    ┌────────────┐                  │
│  │ Poll VLC │───→│ VLC alive? │                  │
│  │ (5s loop)│    └─────┬──────┘                  │
│  └──────────┘          │                         │
│                    ┌───┴───┐                     │
│                    │ Yes   │ No                   │
│                    └───┬───┘                     │
│                        ▼                         │
│              ┌──────────────────┐                │
│              │ Grab keyboard    │                │
│              │ Create uinput    │                │
│              │ Enter event loop │                │
│              │                  │                │
│              │ ┌──────────────┐ │                │
│              │ │ Read event   │ │                │
│              │ │ from /dev/   │ │                │
│              │ │ input        │ │                │
│              │ └──────┬───────┘ │                │
│              │        ▼         │                │
│              │  ┌───────────┐   │                │
│              │  │ F4 held + │   │                │
│              │  │ numpad?   │   │                │
│              │  └──┬────┬───┘   │                │
│              │  Yes│    │No     │                │
│              │     ▼    ▼       │                │
│              │  ┌──┐  ┌─────┐  │                │
│              │  │  │  │Fwd  │  │                │
│              │  │VLC│  │to   │  │                │
│              │  │   │  │uinput │                │
│              │  │CMD│  │     │  │                │
│              │  └──┘  └─────┘  │                │
│              └──────────────────┘                │
│                                                  │
│  On VLC gone: release grab, close uinput         │
└──────────────────────────────────────────────────┘
```

## State machine

```
         ┌──────────────────────┐
         │      IDLE            │
         │  (polling every 5s)  │
         └───────┬──────────────┘
                 │ VLC detected
                 ▼
         ┌──────────────────────┐
         │   GRABBING           │
         │  • Grab /dev/input   │
         │  • Create uinput dev │
         └───────┬──────────────┘
                 │ grab + uinput ready
                 ▼
         ┌──────────────────────┐
         │   ACTIVE             │
         │  • Read raw events   │
         │  • Route / consume   │
         │  • Poll VLC every 2s │
         └───────┬──────────────┘
                 │ VLC gone    │ error
                 ▼              ▼
         ┌──────────────────────┐
         │   RELEASING          │
         │  • Ungrab keyboard   │
         │  • Close uinput      │
         └───────┬──────────────┘
                 │ done
                 ▼
         ┌──────────────────────┐
         │      IDLE            │
         └──────────────────────┘
```

## Edge cases

- **Script starts with VLC already running**: Detection on first poll → grab immediately
- **VLC crashes**: HTTP poll fails → release grab within 2 seconds
- **Stale lock/grab**: If EVIOCGRAB fails (already grabbed by another process), log error and retry
- **F4 held at startup**: No issue — grab happens before any key events are processed
- **Multiple keyboards**: Auto-detect the primary keyboard (look for "keyboard" in device name, skip "Power Button", "Video Bus", etc.)
- **Multiple F4 presses**: Only track state (pressed/released), no counter needed
- **Clean shutdown**: SIGTERM/SIGINT handler releases grab and closes uinput
- **Permission denied**: Detect at startup, log clear message on how to fix (add to input group)

## Script behavior details

### Keyboard detection
Walk `/dev/input/by-path/*-kbd` or enumerate `InputDevice`s, find one with `EV_KEY` capability and "keyboard" in its name. Fall back to first keyboard-capable device. Cache the device path.

### Event forwarding
All `EV_KEY`, `EV_SYN`, `EV_MSC` events from the real keyboard are forwarded to the uinput virtual device, EXCEPT consumed F4+numpad combos.

### F4 state tracking
- Track `f4_pressed` boolean
- On F4 keydown (value 1): set flag, start 500ms timer
- On numpad keydown while flag is set: send VLC command, consume event (don't forward either key)
- On F4 keyup (value 0): clear flag. If no numpad was consumed during this press, forward the F4 keyup event
- On 500ms timeout without numpad press: forward any queued F4 events, clear flag

### VLC detection
Use `requests.get(VLC_URL, auth=("", VLC_PASSWORD), timeout=1)`. If it raises any exception (ConnectionError, Timeout), VLC is not available.

### Logging
Log to stdout for journald integration. Prefix with `[vlc-shortcuts]`. Log level: info on state changes, debug on key events, error on failures.

## File structure

```
Apollo/
├── vlcshort.py            # The daemon script
└── ~/.config/autostart/
    └── vlc-shortcuts.desktop  # XDG autostart (created by user or script)
```

## Dependencies installation

```bash
sudo apt install -y python3-evdev python3-requests
sudo usermod -a -G input $USER
# logout/login for group change to take effect
```

## Testing

- Manual: run `python3 vlcshort.py` in terminal, verify F4+numpad controls VLC
- Verify F4 alone and Alt+F4 still work in other apps
- Verify numpad without F4 works normally
- Verify script auto-detaches and grabs when VLC starts/stops
- Check journal: `journalctl --user -xef | grep vlc-shortcuts`
