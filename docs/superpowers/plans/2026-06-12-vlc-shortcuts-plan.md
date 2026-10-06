# VLC Shortcuts Daemon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A background daemon that captures F4+numpad combos as global VLC hotkeys on Pop OS (Wayland, Linux) without breaking Alt+F4.

**Architecture:** Single Python script using `evdev` for raw keyboard access and `uinput` for event forwarding. Grabs the keyboard exclusively, forwards all events to a virtual device except consumed VLC combos. F4 is forwarded immediately (so Alt+F4 works) — if a numpad key follows within 500ms, the F4 is "undone" via synthetic keyup and the VLC command fires.

**Tech Stack:** Python 3.12, python3-evdev, python3-requests, XDG autostart

---

### Task 1: Install dependencies

**Files:** (none)

- [ ] **Step 1: Install system packages**

Run:
```bash
sudo apt install -y python3-evdev python3-requests
```

Expected: packages install without error.

- [ ] **Step 2: Add user to input group**

```bash
sudo usermod -a -G input $USER
```

Note: user must log out and back in (or reboot) for the group change to take effect. The script will fail with a clear error if the user isn't in the `input` group.

- [ ] **Step 3: Verify uinput module is loaded**

```bash
lsmod | grep uinput
```

If no output, load it:
```bash
sudo modprobe uinput
```

To make it persistent:
```bash
echo uinput | sudo tee /etc/modules-load.d/uinput.conf
```

---

### Task 2: Write the main daemon script

**Files:**
- Create: `vlcshort.py`

The script has three main components:
- **Keyboard detection** — find the primary input device
- **Event loop** — grab keyboard, read events, forward or consume
- **State machine** — idle (polling for VLC) / active (grabbed, forwarding)

- [ ] **Step 1: Write the complete script**

```python
#!/usr/bin/env python3
"""
VLC global shortcuts daemon for Linux.
F4 + Numpad [4-9] controls VLC via HTTP interface.

Uses evdev to grab the keyboard and uinput to forward unconsumed events.
Runs as a background daemon, automatically activates when VLC is detected.

F4 is forwarded immediately on press (preserving Alt+F4). If a numpad key
follows within the timeout window, F4 is "undone" via synthetic keyup and
the VLC command fires instead.
"""

import sys
import time
import logging
import select
import signal

import requests
from evdev import InputDevice, UInput, ecodes as E, list_devices

# ── Configuration ──────────────────────────────────────────────────────────

VLC_URL = "http://localhost:22123/requests/status.xml"
VLC_PASSWORD = "vlc"
IDLE_POLL_SEC = 5       # how often to check for VLC when idle
ACTIVE_POLL_SEC = 2     # how often to re-check VLC when active
F4_WINDOW_SEC = 0.5     # max time after F4 press to wait for numpad

# F4 keycode
KEY_F4 = E.KEY_F4

# Numpad keycodes mapped to (VLC command, extra params)
NUMPAD_BINDINGS = {
    E.KEY_KP4: ("seek", {"val": "-10S"}),
    E.KEY_KP5: ("pl_pause", {}),
    E.KEY_KP6: ("seek", {"val": "+10S"}),
    E.KEY_KP7: ("pl_previous", {}),
    E.KEY_KP8: ("pl_random", {}),
    E.KEY_KP9: ("pl_next", {}),
}

# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[vlc-shortcuts] %(levelname)s: %(message)s",
)
log = logging.getLogger("vlc-shortcuts")


# ── Daemon ─────────────────────────────────────────────────────────────────

class VLCShortcutsDaemon:
    """Background daemon for VLC global hotkeys."""

    def __init__(self):
        self.device: InputDevice | None = None
        self.ui: UInput | None = None
        self.running = True
        self.vlc_available = False

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    # ── Signal handling ────────────────────────────────────────────────────

    def _handle_signal(self, signum, frame):
        log.info("Shutting down...")
        self.running = False

    # ── Keyboard discovery ─────────────────────────────────────────────────

    def find_keyboard(self) -> InputDevice | None:
        """Find the primary physical keyboard device."""
        for path in list_devices():
            try:
                dev = InputDevice(path)
            except (PermissionError, OSError):
                continue

            caps = dev.capabilities()
            if E.EV_KEY not in caps:
                dev.close()
                continue

            key_caps = caps[E.EV_KEY]
            name = dev.name.lower()

            # Filter out non-keyboard devices
            skip_keywords = ("power", "video", "lid", "sleep", "battery")
            if any(kw in name for kw in skip_keywords):
                dev.close()
                continue

            # Must have alphanumeric keys (to skip media remotes etc.)
            if E.KEY_A not in key_caps:
                dev.close()
                continue

            log.info("Found keyboard: %s at %s", dev.name, dev.path)
            return dev

        log.error("No suitable keyboard found. Ensure you are in the 'input' group.")
        return None

    # ── VLC HTTP API ───────────────────────────────────────────────────────

    def check_vlc(self) -> bool:
        """Return True if VLC's HTTP interface is responding."""
        try:
            resp = requests.get(VLC_URL, auth=("", VLC_PASSWORD), timeout=1)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def send_vlc_command(self, command: str, **params):
        """Send a command to VLC via its HTTP API."""
        try:
            requests.get(
                VLC_URL,
                params={"command": command, **params},
                auth=("", VLC_PASSWORD),
                timeout=1,
            )
        except requests.RequestException as exc:
            log.error("VLC command failed (%s %s): %s", command, params, exc)

    # ── Active event loop (keyboard grabbed) ──────────────────────────────

    def _active_loop(self):
        """Run while VLC is active: grab keyboard, handle shortcuts."""
        assert self.device is not None

        try:
            self.device.grab()
        except OSError as exc:
            log.error("Failed to grab keyboard: %s", exc)
            return

        log.info("Keyboard grabbed — F4+numpad shortcuts active")

        try:
            self.ui = UInput.from_device(
                self.device, name="vlc-shortcuts-virtual"
            )
        except OSError as exc:
            log.error("Failed to create uinput device: %s", exc)
            self.device.ungrab()
            return

        try:
            self._event_loop()
        finally:
            if self.ui is not None:
                self.ui.close()
                self.ui = None
            self.device.ungrab()
            log.info("Keyboard released")

    def _event_loop(self):
        """Core event dispatch loop."""
        assert self.device is not None
        assert self.ui is not None

        poll = select.poll()
        poll.register(self.device.fd(), select.POLLIN)

        f4_down = False
        f4_consumed = False
        f4_down_time = 0.0

        while self.running and self.vlc_available:
            # Poll with timeout so we can periodically re-check VLC
            ready = poll.poll(ACTIVE_POLL_SEC * 1000)

            if not ready:
                # Timeout — verify VLC is still running
                if not self.check_vlc():
                    log.info("VLC no longer responding — releasing")
                    self.vlc_available = False
                continue

            # Read available events
            for event in self.device.read():
                if event.type != E.EV_KEY:
                    # Non-key event: forward unconditionally
                    self.ui.write_event(event)
                    self.ui.syn()
                    continue

                key = event.code
                val = event.value  # 0=up, 1=down, 2=repeat

                # ── F4 handling ──────────────────────────────────────────
                if key == KEY_F4:
                    if val == 1:
                        # F4 pressed — forward immediately (preserves Alt+F4)
                        f4_down = True
                        f4_consumed = False
                        f4_down_time = time.monotonic()
                        self._forward_key_event(KEY_F4, 1)
                    elif val == 0:
                        # F4 released
                        if f4_down and not f4_consumed:
                            # Normal F4 tap — forward the release
                            self._forward_key_event(KEY_F4, 0)
                        f4_down = False

                # ── Numpad handling (only when F4 is held) ──────────────
                elif key in NUMPAD_BINDINGS and f4_down and not f4_consumed:
                    if val == 1:
                        elapsed = time.monotonic() - f4_down_time
                        if elapsed <= F4_WINDOW_SEC:
                            cmd, params = NUMPAD_BINDINGS[key]
                            log.info("VLC: %s %s", cmd, params)
                            self.send_vlc_command(cmd, **params)
                            f4_consumed = True
                            # Undo the F4 press we already forwarded
                            self._forward_key_event(KEY_F4, 0)
                    # Numpad repeat/hold events are ignored while consumed

                # ── All other keys ──────────────────────────────────────
                else:
                    self._forward_key_event(key, val)

    def _forward_key_event(self, keycode: int, value: int):
        """Write a single EV_KEY event and SYN to the virtual device."""
        assert self.ui is not None
        self.ui.write(E.EV_KEY, keycode, value)
        self.ui.write(E.EV_SYN, E.SYN_REPORT, 0)

    # ── Idle loop ───────────────────────────────────────────────────────────

    def _idle_loop(self):
        """Poll until VLC is detected."""
        log.info("Idle — waiting for VLC…")
        while self.running and not self.vlc_available:
            if self.check_vlc():
                self.vlc_available = True
                log.info("VLC detected!")
                return
            time.sleep(IDLE_POLL_SEC)

    # ── Main ────────────────────────────────────────────────────────────────

    def run(self):
        """Main entry point — runs until SIGINT/SIGTERM."""
        log.info("Daemon started — pid %d", os.getpid())
        log.info("Shortcuts: F4 + Numpad [4-9] to control VLC")

        while self.running:
            self._idle_loop()
            if not self.running:
                break

            self.device = self.find_keyboard()
            if self.device is None:
                log.warning(
                    "No keyboard found. Check 'input' group membership "
                    "and /dev/input permissions. Retrying in %ds…",
                    IDLE_POLL_SEC,
                )
                time.sleep(IDLE_POLL_SEC)
                self.vlc_available = False
                continue

            try:
                self._active_loop()
            except Exception:
                log.exception("Unexpected error in active loop")
            finally:
                if self.device is not None:
                    self.device.close()
                    self.device = None
                self.vlc_available = False

        log.info("Daemon stopped")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    daemon = VLCShortcutsDaemon()
    daemon.run()
```

- [ ] **Step 2: Make the script executable**

```bash
chmod +x vlcshort.py
```

---

### Task 3: Test the script manually

**Files:** (none — manual testing)

- [ ] **Step 1: Run the script in a terminal**

Ensure VLC is running with its HTTP interface enabled (Tools → Preferences → Interface → Main interfaces → HTTP remote control, set a password).

Kill any existing VLC, start it fresh with:
```bash
vlc --extraintf=http --http-password=vlc &
```

Then run the daemon:
```bash
python3 vlcshort.py
```

Expected: logs "VLC detected!" and "Keyboard grabbed — F4+numpad shortcuts active"

- [ ] **Step 2: Test each shortcut**

With VLC playing a file, press each combo and verify:
- `F4 + Num9` → next track
- `F4 + Num8` → toggle random mode
- `F4 + Num7` → previous track
- `F4 + Num6` → seek forward 10s
- `F4 + Num5` → play/pause
- `F4 + Num4` → seek backward 10s

- [ ] **Step 3: Test Alt+F4 still works**

While daemon is running:
1. Open any application (e.g., gedit, Nautilus)
2. Press `Alt+F4` — window should close normally

- [ ] **Step 4: Test numpad without F4**

Open a text editor. Type on the numpad — digits should appear normally.

- [ ] **Step 5: Test daemon releases on VLC stop**

Kill VLC or close it. Daemon should log "VLC no longer responding" and "Keyboard released". Verify keyboard is fully normal again.

- [ ] **Step 6: Test daemon re-grabs on VLC restart**

Restart VLC. Daemon should re-detect and grab again.

- [ ] **Step 7: Stop the daemon**

Press `Ctrl+C` — should cleanly ungrab and exit.

---

### Task 4: Set up XDG autostart

**Files:**
- Create: `/home/shaarky/.config/autostart/vlc-shortcuts.desktop`

- [ ] **Step 1: Create the autostart entry**

```bash
mkdir -p ~/.config/autostart
```

Write `~/.config/autostart/vlc-shortcuts.desktop`:

```desktop
[Desktop Entry]
Type=Application
Name=VLC Shortcuts Daemon
Comment=Global F4+numpad hotkeys for VLC
Exec=/media/shaarky/Data/Projects/Apollo/vlcshort.py
Terminal=false
X-GNOME-Autostart-enabled=true
```

- [ ] **Step 2: Test autostart**

Log out and back in (or test with):
```bash
gtk-launch vlc-shortcuts.desktop
```

Or verify the file is picked up:
```bash
ls -la ~/.config/autostart/vlc-shortcuts.desktop
```

- [ ] **Step 3: Test reboot persistence**

Reboot, start VLC, and verify the shortcuts work without manually running anything.
