"""
Verification Tool  –  EID / S/N / IMEI comparator
Requires: customtkinter, pillow, pytesseract
  pip install customtkinter pillow pytesseract
"""

import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
import pytesseract
from PIL import Image

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

BG           = "#6B9DC2"   # steel-blue background
ENTRY_BG     = "#D6D6D6"   # light-grey inputs
TABLE_BG     = "#D6D6D6"
BTN_GREEN    = "#5BC954"
BTN_GREEN_HV = "#4CAF50"
BTN_WHITE    = "#FFFFFF"
BTN_WHITE_HV = "#E8E8E8"


# ─────────────────────────────────────────────
#  ADB HELPERS
# ─────────────────────────────────────────────
def _adb(*args, timeout: int = 12) -> str:
    try:
        return subprocess.check_output(
            [ADB, *args], stderr=subprocess.DEVNULL, timeout=timeout
        ).decode(errors="replace").strip()
    except Exception:
        return ""


def fetch_eid() -> str:
    """Try several strategies to read the eUICC EID from the device."""
    # Strategy 1: direct getprop
    for prop in ("gsm.sim.eid", "persist.radio.eid0", "persist.radio.eid"):
        v = _adb("shell", "getprop", prop)
        if v and len(v) > 10:
            return v

    # Strategy 2: dumpsys isub
    for line in _adb("shell", "dumpsys", "isub").splitlines():
        lw = line.lower()
        if "eid" in lw and "=" in lw:
            val = line.split("=")[-1].strip().strip('"')
            if val and len(val) > 10:
                return val

    return "Not Found"


def fetch_serial() -> str:
    v = _adb("get-serialno")
    if v and v != "unknown":
        return v
    return _adb("shell", "getprop", "ro.serialno") or "Not Found"


def fetch_imei() -> str:
    """OCR-based IMEI fetch (existing approach) with a fast ADB fallback."""
    # ---- fast path: service call iphonesubinfo ----
    try:
        raw = _adb("shell", "service", "call", "iphonesubinfo", "1")
        digits = "".join(
            ch for ch in raw if ch.isdigit() or ch == "."
        ).replace(".", "")
        if len(digits) >= 15:
            return digits[:15]
    except Exception:
        pass

    # ---- OCR path (original logic) ----
    _adb("shell", "am", "start", "-a", "android.settings.DEVICE_INFO_SETTINGS")
    time.sleep(3)
    _adb("shell", "input", "swipe", "500", "1500", "500", "500")
    time.sleep(2)
    _adb("shell", "input", "tap", "400", "1000")
    time.sleep(3)
    _adb("shell", "screencap", "/sdcard/screen.png")
    _adb("pull", "/sdcard/screen.png")

    try:
        data = pytesseract.image_to_data(
            Image.open("screen.png"),
            output_type=pytesseract.Output.DICT,
        )
        for text in data["text"]:
            text = text.strip()
            if text.isdigit() and len(text) >= 15:
                return text
    except Exception:
        pass

    return "Not Found"


def fetch_device_info() -> list[tuple[str, str]]:
    serial       = _adb("get-serialno")          or "N/A"
    brand        = _adb("shell", "getprop", "ro.product.brand")          or "N/A"
    model        = _adb("shell", "getprop", "ro.product.model")          or "N/A"
    android_ver  = _adb("shell", "getprop", "ro.build.version.release")  or "N/A"

    battery = "N/A"
    for ln in _adb("shell", "dumpsys", "battery").splitlines():
        if "level:" in ln:
            battery = ln.split(":")[-1].strip() + " %"
            break

    wifi_mac = "N/A"
    for ln in _adb("shell", "ip", "addr", "show", "wlan0").splitlines():
        if "link/ether" in ln:
            wifi_mac = ln.split()[1]
            break

    bt_mac = (
        _adb("shell", "settings", "get", "secure", "bluetooth_address") or "N/A"
    )

    return [
        ("Serial No",       serial),
        ("Brand",           brand),
        ("Model",           model),
        ("Android Version", android_ver),
        ("Battery",         battery),
        ("WiFi MAC",        wifi_mac),
        ("Bluetooth MAC",   bt_mac),
    ]


# ─────────────────────────────────────────────
#  APPLICATION
# ─────────────────────────────────────────────
class App(ctk.CTk):
    """Main verification window – pixel-faithful to the provided mockup."""

    # Field definitions: (display label, internal key, fetch function)
    FIELDS = [
        ("Scan box EID :",  "eid",  fetch_eid),
        ("Scan box S/N :",  "sn",   fetch_serial),
        ("Scan box IMEI :", "imei", fetch_imei),
    ]

    def __init__(self):
        super().__init__()
        self.title("Verification Tool")
        self.geometry("760x700")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        ctk.set_appearance_mode("light")

        # widget registries
        self._entries:        dict[str, ctk.CTkEntry] = {}
        self._fetched_lbls:   dict[str, ctk.CTkLabel] = {}
        self._fail_lbls:      dict[str, ctk.CTkLabel] = {}
        self._pass_lbls:      dict[str, ctk.CTkLabel] = {}

        self._build()

    # ── layout ──────────────────────────────────────────────────────
    def _build(self):
        # ── Title ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="verification tool",
            font=ctk.CTkFont("Segoe UI", 22),
            text_color="white", fg_color="transparent"
        ).pack(pady=(22, 14))

        # ── Input rows ───────────────────────────────────────────────
        rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        rows_frame.pack(padx=30, fill="x")

        for label_text, key, _ in self.FIELDS:
            self._build_row(rows_frame, label_text, key)

        # ── Action buttons ───────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=22)

        self._btn_fetch = ctk.CTkButton(
            btn_row, text="Fetch & Compare",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=BTN_GREEN, hover_color=BTN_GREEN_HV,
            text_color="black",
            border_color="#3A9E3A", border_width=2,
            width=210, height=46, corner_radius=10,
            command=self._on_fetch
        )
        self._btn_fetch.pack(side="left", padx=14)

        self._btn_clear = ctk.CTkButton(
            btn_row, text="Clear",
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color=BTN_WHITE, hover_color=BTN_WHITE_HV,
            text_color="black",
            border_color="#BBBBBB", border_width=1,
            width=130, height=46, corner_radius=10,
            command=self._clear
        )
        self._btn_clear.pack(side="left", padx=4)

        # ── PASS / FAIL label ────────────────────────────────────────
        self._result_lbl = ctk.CTkLabel(
            self, text="PASS/FAIL",
            font=ctk.CTkFont("Segoe UI", 34, "bold"),
            text_color="black", fg_color="transparent"
        )
        self._result_lbl.pack(pady=(6, 10))

        # ── Device-info table ────────────────────────────────────────
        table_container = ctk.CTkFrame(
            self, fg_color=TABLE_BG, corner_radius=8
        )
        table_container.pack(padx=20, fill="both", expand=True, pady=(6, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Vt.Treeview",
            background=TABLE_BG,
            fieldbackground=TABLE_BG,
            foreground="#1a1a1a",
            rowheight=30,
            font=("Segoe UI", 11),
            borderwidth=0,
        )
        style.configure(
            "Vt.Treeview.Heading",
            background="#BEBEBE",
            foreground="#1a1a1a",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.map("Vt.Treeview", background=[("selected", "#A8C8E8")])

        self._tree = ttk.Treeview(
            table_container,
            columns=("Key", "Value"),
            show="headings",
            height=7,
            style="Vt.Treeview",
        )
        self._tree.heading("Key",   text="Property")
        self._tree.heading("Value", text="Value")
        self._tree.column("Key",   width=210, anchor="w")
        self._tree.column("Value", width=480, anchor="w")
        self._tree.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Get Info button ──────────────────────────────────────────
        self._btn_info = ctk.CTkButton(
            self, text="Get Info",
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color=BTN_WHITE, hover_color=BTN_WHITE_HV,
            text_color="black",
            border_color="#BBBBBB", border_width=1,
            width=160, height=42, corner_radius=10,
            command=self._on_get_info
        )
        self._btn_info.pack(pady=12)

    def _build_row(self, parent: ctk.CTkFrame, label_text: str, key: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        # label
        ctk.CTkLabel(
            row, text=label_text,
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="#111111", fg_color="transparent",
            width=148, anchor="w"
        ).pack(side="left")

        # input entry
        entry = ctk.CTkEntry(
            row, width=230,
            fg_color=ENTRY_BG, border_color="#BBBBBB",
            text_color="#111111", height=36, corner_radius=8
        )
        entry.pack(side="left", padx=(0, 18))
        self._entries[key] = entry

        # fetched-value display  (ADB result shown after compare)
        fetched_lbl = ctk.CTkLabel(
            row, text="— — —",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#4a4a4a", fg_color="transparent",
            width=130, anchor="w"
        )
        fetched_lbl.pack(side="left")
        self._fetched_lbls[key] = fetched_lbl

        # status icons  ✗  ✓
        icons = ctk.CTkFrame(row, fg_color="transparent")
        icons.pack(side="left", padx=6)

        fail_lbl = ctk.CTkLabel(
            icons, text="✗",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color="#CC2222", fg_color="transparent", width=26
        )
        fail_lbl.pack(side="left", padx=2)
        self._fail_lbls[key] = fail_lbl

        pass_lbl = ctk.CTkLabel(
            icons, text="✓",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color="#888888", fg_color="transparent", width=26
        )
        pass_lbl.pack(side="left", padx=2)
        self._pass_lbls[key] = pass_lbl

    # ── logic ────────────────────────────────────────────────────────
    def _set_status(self, key: str, state: str):
        """state: 'pass' | 'fail' | 'idle'"""
        if state == "pass":
            self._fail_lbls[key].configure(text_color="#AAAAAA")
            self._pass_lbls[key].configure(text_color="#42EE42")
        elif state == "fail":
            self._fail_lbls[key].configure(text_color="#CC2222")
            self._pass_lbls[key].configure(text_color="#AAAAAA")
        else:  # idle
            self._fail_lbls[key].configure(text_color="#CC2222")
            self._pass_lbls[key].configure(text_color="#888888")

    def _set_ui_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for btn in (self._btn_fetch, self._btn_clear, self._btn_info):
            btn.configure(state=state)

    # ── Fetch & Compare ──────────────────────────────────────────────
    def _on_fetch(self):
        inputs = {key: self._entries[key].get().strip() for key, *_ in
                  [(k,) for _, k, _ in self.FIELDS]}
        if not any(inputs.values()):
            messagebox.showwarning("Input Required",
                                   "Enter at least one value to compare.")
            return

        self._result_lbl.configure(text="Fetching…", text_color="#333333")
        self._set_ui_busy(True)

        def worker():
            verdicts: list[bool] = []
            for _, key, fn in self.FIELDS:
                scanned = self._entries[key].get().strip()
                if not scanned:
                    # nothing entered – skip this field
                    self.after(0, lambda k=key: (
                        self._fetched_lbls[k].configure(text="— — —"),
                        self._set_status(k, "idle")
                    ))
                    continue

                fetched = fn()
                match = (scanned == fetched) and fetched != "Not Found"
                verdicts.append(match)

                status = "pass" if match else "fail"
                display = fetched

                self.after(0, lambda k=key, v=display, s=status: (
                    self._fetched_lbls[k].configure(text=v),
                    self._set_status(k, s),
                ))

            self.after(0, lambda: self._finish_compare(verdicts))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_compare(self, verdicts: list[bool]):
        if not verdicts:
            self._result_lbl.configure(text="PASS/FAIL", text_color="black")
        elif all(verdicts):
            self._result_lbl.configure(text="✅  PASS", text_color="#1A7A1A")
        else:
            self._result_lbl.configure(text="❌  FAIL", text_color="#BB0000")
        self._set_ui_busy(False)

    # ── Clear ────────────────────────────────────────────────────────
    def _clear(self):
        for entry in self._entries.values():
            entry.delete(0, tk.END)
        for _, key, _ in self.FIELDS:
            self._fetched_lbls[key].configure(text="— — —")
            self._set_status(key, "idle")
        self._result_lbl.configure(text="PASS/FAIL", text_color="black")
        self._tree.delete(*self._tree.get_children())

    # ── Get Info ─────────────────────────────────────────────────────
    def _on_get_info(self):
        self._tree.delete(*self._tree.get_children())
        self._tree.insert("", "end", values=("Loading…", "Please wait"))
        self._set_ui_busy(True)

        def worker():
            data = fetch_device_info()
            self.after(0, lambda: self._populate_tree(data))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_tree(self, data: list[tuple[str, str]]):
        self._tree.delete(*self._tree.get_children())
        for row in data:
            self._tree.insert("", "end", values=row)
        self._set_ui_busy(False)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()