import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import pytesseract
from PIL import Image
from exl import ExcelVerifyWindow

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"
BG  = "#6B9DC2"

ctk.set_appearance_mode("light")

# ───────────────────────────────────────────
#  ADB FETCH FUNCTIONS
# ───────────────────────────────────────────

def adb(*args):
    try:
        return subprocess.check_output([ADB, *args], stderr=subprocess.DEVNULL, timeout=12).decode().strip()
    except:
        return ""

def fetch_eid():
    for prop in ("gsm.sim.eid", "persist.radio.eid0", "persist.radio.eid"):
        v = adb("shell", "getprop", prop)
        if v and len(v) > 10:
            return v
    return "Not Found"

def fetch_serial():
    v = adb("get-serialno")
    return v if v and v != "unknown" else "Not Found"

def fetch_imei():
    # Fast path
    raw = adb("shell", "service", "call", "iphonesubinfo", "1")
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) >= 15:
        return digits[:15]

    # OCR fallback
    adb("shell", "am", "start", "-a", "android.settings.DEVICE_INFO_SETTINGS")
    time.sleep(3)
    adb("shell", "input", "swipe", "500", "1500", "500", "500")
    time.sleep(2)
    adb("shell", "input", "tap", "400", "1000")
    time.sleep(3)
    adb("shell", "screencap", "/sdcard/screen.png")
    adb("pull", "/sdcard/screen.png")
    try:
        data = pytesseract.image_to_data(Image.open("screen.png"), output_type=pytesseract.Output.DICT)
        for t in data["text"]:
            if t.strip().isdigit() and len(t.strip()) >= 15:
                return t.strip()
    except:
        pass
    return "Not Found"

def fetch_device_info():
    battery = "N/A"
    for line in adb("shell", "dumpsys", "battery").splitlines():
        if "level:" in line:
            battery = line.split(":")[-1].strip() + " %"
            break

    wifi = "N/A"
    for line in adb("shell", "ip", "addr", "show", "wlan0").splitlines():
        if "link/ether" in line:
            wifi = line.split()[1]
            break

    return [
        ("Serial No",       adb("get-serialno")                              or "N/A"),
        ("Brand",           adb("shell", "getprop", "ro.product.brand")      or "N/A"),
        ("Model",           adb("shell", "getprop", "ro.product.model")      or "N/A"),
        ("Android Version", adb("shell", "getprop", "ro.build.version.release") or "N/A"),
        ("Battery",         battery),
        ("WiFi MAC",        wifi),
        ("Bluetooth MAC",   adb("shell", "settings", "get", "secure", "bluetooth_address") or "N/A"),
    ]

# ───────────────────────────────────────────
#  MAIN GUI
# ───────────────────────────────────────────

root = ctk.CTk()
root.title("Verification Tool")
root.geometry("740x680")
root.resizable(False, False)
root.configure(fg_color=BG)

# ── File Menu ────────────────────────────────
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Excel Verification", command=lambda: ExcelVerifyWindow(root))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# Title
ctk.CTkLabel(root, text="verification tool", font=ctk.CTkFont("Segoe UI", 22),
             text_color="white", fg_color="transparent").pack(pady=(22, 14))

# ── Input rows ──────────────────────────────
rows_frame = ctk.CTkFrame(root, fg_color="transparent")
rows_frame.pack(padx=30, fill="x")

fields = [("Scan box EID :", "eid"), ("Scan box S/N :", "sn"), ("Scan box IMEI :", "imei")]
entries, fetched_lbls, fail_lbls, pass_lbls = {}, {}, {}, {}

for label, key in fields:
    row = ctk.CTkFrame(rows_frame, fg_color="transparent")
    row.pack(fill="x", pady=6)

    ctk.CTkLabel(row, text=label, font=ctk.CTkFont("Segoe UI", 14),
                 text_color="#111", fg_color="transparent", width=148, anchor="w").pack(side="left")

    entries[key] = ctk.CTkEntry(row, width=230, fg_color="#D6D6D6", border_color="#BBBBBB",
                                 text_color="#111", height=36, corner_radius=8)
    entries[key].pack(side="left", padx=(0, 18))

    fetched_lbls[key] = ctk.CTkLabel(row, text="— — —", font=ctk.CTkFont("Segoe UI", 12),
                                      text_color="#4a4a4a", fg_color="transparent", width=130, anchor="w")
    fetched_lbls[key].pack(side="left")

    icon_frame = ctk.CTkFrame(row, fg_color="transparent")
    icon_frame.pack(side="left", padx=6)

    fail_lbls[key] = ctk.CTkLabel(icon_frame, text="✗", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                                   text_color="#CC2222", fg_color="transparent", width=26)
    fail_lbls[key].pack(side="left", padx=2)

    pass_lbls[key] = ctk.CTkLabel(icon_frame, text="✓", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                                   text_color="#888", fg_color="transparent", width=26)
    pass_lbls[key].pack(side="left", padx=2)

# ── Buttons ─────────────────────────────────
btn_row = ctk.CTkFrame(root, fg_color="transparent")
btn_row.pack(pady=22)

btn_fetch = ctk.CTkButton(btn_row, text="Fetch & Compare", font=ctk.CTkFont("Segoe UI", 14, "bold"),
                           fg_color="#5BC954", hover_color="#4CAF50", text_color="black",
                           border_color="#3A9E3A", border_width=2, width=210, height=46, corner_radius=10)
btn_fetch.pack(side="left", padx=14)

btn_clear = ctk.CTkButton(btn_row, text="Clear", font=ctk.CTkFont("Segoe UI", 14),
                           fg_color="white", hover_color="#E8E8E8", text_color="black",
                           border_color="#BBB", border_width=1, width=130, height=46, corner_radius=10)
btn_clear.pack(side="left", padx=4)

# ── Result label ─────────────────────────────
result_lbl = ctk.CTkLabel(root, text="PASS / FAIL", font=ctk.CTkFont("Segoe UI", 34, "bold"),
                           text_color="black", fg_color="transparent")
result_lbl.pack(pady=(6, 10))

# ── Device info table ────────────────────────
table_frame = ctk.CTkFrame(root, fg_color="#D6D6D6", corner_radius=8)
table_frame.pack(padx=20, fill="both", expand=True, pady=(4, 4))

style = ttk.Style()
style.theme_use("clam")
style.configure("T.Treeview", background="#D6D6D6", fieldbackground="#D6D6D6",
                font=("Segoe UI", 11), rowheight=30, borderwidth=0)
style.configure("T.Treeview.Heading", background="#BEBEBE", font=("Segoe UI", 11, "bold"), relief="flat")
style.map("T.Treeview", background=[("selected", "#A8C8E8")])

tree = ttk.Treeview(table_frame, columns=("Key", "Value"), show="headings", height=7, style="T.Treeview")
tree.heading("Key", text="Property")
tree.heading("Value", text="Value")
tree.column("Key", width=210, anchor="w")
tree.column("Value", width=460, anchor="w")
tree.pack(fill="both", expand=True, padx=2, pady=2)

# ── Get Info button ──────────────────────────
btn_info = ctk.CTkButton(root, text="Get Info", font=ctk.CTkFont("Segoe UI", 14),
                          fg_color="white", hover_color="#E8E8E8", text_color="black",
                          border_color="#BBB", border_width=1, width=160, height=42, corner_radius=10)
btn_info.pack(pady=12)

# ───────────────────────────────────────────
#  ACTIONS
# ───────────────────────────────────────────

FETCH_FN = {"eid": fetch_eid, "sn": fetch_serial, "imei": fetch_imei}

def set_busy(busy):
    state = "disabled" if busy else "normal"
    for b in (btn_fetch, btn_clear, btn_info):
        b.configure(state=state)

def set_status(key, passed):
    if passed:
        fail_lbls[key].configure(text_color="#AAAAAA")
        pass_lbls[key].configure(text_color="#1E8A1E")
    else:
        fail_lbls[key].configure(text_color="#CC2222")
        pass_lbls[key].configure(text_color="#AAAAAA")

def reset_status(key):
    fail_lbls[key].configure(text_color="#CC2222")
    pass_lbls[key].configure(text_color="#888888")

def on_fetch():
    scanned = {key: entries[key].get().strip() for key in entries}

    if not all(scanned.values()):
        messagebox.showwarning("Input Required", "Please fill in all three fields before comparing.")
        return

    result_lbl.configure(text="Fetching…", text_color="#333")
    set_busy(True)

    def worker():
        results = {}
        for key, value in scanned.items():
            fetched = FETCH_FN[key]()
            matched = (value == fetched) and fetched != "Not Found"
            results[key] = (fetched, matched)
            root.after(0, lambda k=key, f=fetched, m=matched: (
                fetched_lbls[k].configure(text=f),
                set_status(k, m)
            ))

        all_pass = all(m for _, m in results.values())
        root.after(0, lambda: (
            result_lbl.configure(
                text="✅  PASS" if all_pass else "❌  FAIL",
                text_color="#1A7A1A" if all_pass else "#BB0000"
            ),
            set_busy(False)
        ))

    threading.Thread(target=worker, daemon=True).start()

def on_clear():
    for key in entries:
        entries[key].delete(0, tk.END)
        fetched_lbls[key].configure(text="— — —")
        reset_status(key)
    result_lbl.configure(text="PASS / FAIL", text_color="black")
    tree.delete(*tree.get_children())

def on_get_info():
    tree.delete(*tree.get_children())
    tree.insert("", "end", values=("Loading…", "Please wait"))
    set_busy(True)

    def worker():
        data = fetch_device_info()
        root.after(0, lambda: (
            tree.delete(*tree.get_children()),
            [tree.insert("", "end", values=row) for row in data],
            set_busy(False)
        ))

    threading.Thread(target=worker, daemon=True).start()

btn_fetch.configure(command=on_fetch)
btn_clear.configure(command=on_clear)
btn_info.configure(command=on_get_info)

root.mainloop()