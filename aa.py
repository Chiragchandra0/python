import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"
BG = "#6B9DC2"

ctk.set_appearance_mode("light")

# ───────────────────────────────────────────
#  ADB COMMANDS
# ───────────────────────────────────────────

def adb_cmd(*args):
    """Execute ADB command"""
    try:
        return subprocess.check_output([ADB, *args], stderr=subprocess.DEVNULL, timeout=10).decode().strip()
    except:
        return "Not Found"

def fetch_eid():
    """Get EID from device via ADB"""
    for prop in ("gsm.sim.eid", "persist.radio.eid0", "persist.radio.eid"):
        v = adb_cmd("shell", "getprop", prop)
        if v and len(v) > 10:
            return v
    return "Not Found"

def fetch_serial():
    """Get Serial Number from device via ADB"""
    v = adb_cmd("get-serialno")
    return v if v and v != "unknown" else "Not Found"

def fetch_imei():
    """Get IMEI from device via ADB only (no OCR)"""
    # Method 1: service call iphonesubinfo
    raw = adb_cmd("shell", "service", "call", "iphonesubinfo", "1")
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) >= 15:
        return digits[:15]
    
    # Method 2: getprop
    imei = adb_cmd("shell", "getprop", "ro.telephony.default_network")
    if imei and len(imei) >= 15:
        return imei[:15]
    
    return "Not Found"

# ───────────────────────────────────────────
#  EXCEL VERIFICATION WINDOW (Separate)
# ───────────────────────────────────────────

class ExcelVerifyWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Excel Device Verification")
        self.geometry("850x650")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.excel_data = None
        self.excel_file = None
        self._build()

    def _build(self):
        # Title
        ctk.CTkLabel(self, text="Excel Device Verification", font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color="white", fg_color="transparent").pack(pady=(16, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=10, fill="x")

        self.btn_import = ctk.CTkButton(btn_frame, text="📁 Import Excel", font=ctk.CTkFont("Segoe UI", 12),
                                        fg_color="white", hover_color="#E8E8E8", text_color="black",
                                        border_color="#BBB", border_width=1, width=140, height=38, corner_radius=8,
                                        command=self._import_excel)
        self.btn_import.pack(side="left", padx=8)

        self.btn_verify = ctk.CTkButton(btn_frame, text="✓ Verify", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                        fg_color="#5BC954", hover_color="#4CAF50", text_color="black",
                                        border_color="#3A9E3A", border_width=2, width=140, height=38, corner_radius=8,
                                        command=self._verify)
        self.btn_verify.pack(side="left", padx=8)

        self.file_label = ctk.CTkLabel(btn_frame, text="No file selected", font=ctk.CTkFont("Segoe UI", 11),
                                       text_color="#FFF", fg_color="transparent")
        self.file_label.pack(side="left", padx=15)

        # Result label
        self.result_lbl = ctk.CTkLabel(self, text="MATCH / NOT MATCH", font=ctk.CTkFont("Segoe UI", 28, "bold"),
                                       text_color="black", fg_color="transparent")
        self.result_lbl.pack(pady=10)

        # Table
        table_frame = ctk.CTkFrame(self, fg_color="#D6D6D6", corner_radius=8)
        table_frame.pack(padx=20, fill="both", expand=True, pady=(8, 12))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("E.Treeview", background="#D6D6D6", fieldbackground="#D6D6D6",
                        font=("Segoe UI", 10), rowheight=28, borderwidth=0)
        style.configure("E.Treeview.Heading", background="#BEBEBE", font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("E.Treeview", background=[("selected", "#A8C8E8")])

        self.tree = ttk.Treeview(table_frame, columns=("Field", "Device Value", "Excel Value", "Status"),
                                 show="headings", height=16, style="E.Treeview")
        self.tree.heading("Field", text="Field")
        self.tree.heading("Device Value", text="Device Value")
        self.tree.heading("Excel Value", text="Excel Value")
        self.tree.heading("Status", text="Match")
        self.tree.column("Field", width=140, anchor="w")
        self.tree.column("Device Value", width=220, anchor="w")
        self.tree.column("Excel Value", width=220, anchor="w")
        self.tree.column("Status", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

    def _import_excel(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            title="Select Excel File"
        )
        if not file_path:
            return
        try:
            self.excel_data = pd.read_excel(file_path)
            self.excel_file = file_path.split("/")[-1]
            self.file_label.configure(text=f"✓ {self.excel_file}")
            messagebox.showinfo("Success", f"Loaded: {self.excel_file}\n{len(self.excel_data)} rows")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")

    def _verify(self):
        if self.excel_data is None:
            messagebox.showwarning("No File", "Please import Excel file first.")
            return

        self.result_lbl.configure(text="Verifying…", text_color="#333")
        self.btn_verify.configure(state="disabled")
        self.btn_import.configure(state="disabled")

        def worker():
            # Get device properties
            device_props = {
                "Model Number": adb_cmd("shell", "getprop", "ro.product.model"),
                "AP Version": adb_cmd("shell", "getprop", "ro.build.version.release"),
                "CP Version": adb_cmd("shell", "getprop", "ro.baseband"),
                "CSP Version": adb_cmd("shell", "getprop", "ro.build.display.id"),
            }
            model = device_props.get("Model Number", "").strip()

            if not model or model == "Not Found":
                self.after(0, lambda: messagebox.showerror("Error", "Could not fetch Model Number from device."))
                self.after(0, lambda: (self.btn_verify.configure(state="normal"), 
                                      self.btn_import.configure(state="normal")))
                return

            # Find matching row in Excel
            matching_row = None
            for idx, row in self.excel_data.iterrows():
                if str(row.get("Model Number", "")).strip().upper() == model.upper():
                    matching_row = row
                    break

            if matching_row is None:
                self.after(0, lambda: messagebox.showwarning("Not Found", f"Model '{model}' not found in Excel."))
                self.after(0, lambda: (self.btn_verify.configure(state="normal"), 
                                      self.btn_import.configure(state="normal")))
                return

            # Compare fields
            fields = ["Model Number", "AP Version", "CP Version", "CSP Version"]
            results = []
            all_match = True

            for field in fields:
                device_val = str(device_props.get(field, "N/A")).strip().upper()
                excel_val = str(matching_row.get(field, "N/A")).strip().upper()
                match = device_val == excel_val
                status = "✓" if match else "✗"
                results.append((field, device_val, excel_val, status))
                if not match:
                    all_match = False

            # Update UI
            self.after(0, lambda: (
                self.tree.delete(*self.tree.get_children()),
                [self.tree.insert("", "end", values=r) for r in results],
                self.result_lbl.configure(
                    text="✅  MATCH" if all_match else "❌  NOT MATCH",
                    text_color="#1A7A1A" if all_match else "#BB0000"
                ),
                self.btn_verify.configure(state="normal"),
                self.btn_import.configure(state="normal")
            ))

        threading.Thread(target=worker, daemon=True).start()

# ───────────────────────────────────────────
#  MAIN WINDOW (EID Verification)
# ───────────────────────────────────────────

root = ctk.CTk()
root.title("Device Verification System")
root.geometry("750x600")
root.resizable(False, False)
root.configure(fg_color=BG)

# File Menu
menubar = tk.Menu(root)
root.config(menu=menubar)
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Excel Verification", command=lambda: ExcelVerifyWindow(root))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# Title
ctk.CTkLabel(root, text="EID / S/N / IMEI Verification", font=ctk.CTkFont("Segoe UI", 22, "bold"),
             text_color="white", fg_color="transparent").pack(pady=(20, 25))

# ─── Input rows ──────────────────────────
rows_frame = ctk.CTkFrame(root, fg_color="transparent")
rows_frame.pack(padx=30, fill="x")

fields = [("Scan EID :", "eid"), ("Scan S/N :", "sn"), ("Scan IMEI :", "imei")]
entries, fetched_lbls, fail_lbls, pass_lbls = {}, {}, {}, {}

for label, key in fields:
    row = ctk.CTkFrame(rows_frame, fg_color="transparent")
    row.pack(fill="x", pady=6)

    ctk.CTkLabel(row, text=label, font=ctk.CTkFont("Segoe UI", 14),
                 text_color="#111", fg_color="transparent", width=130, anchor="w").pack(side="left")

    entries[key] = ctk.CTkEntry(row, width=220, fg_color="#D6D6D6", border_color="#BBBBBB",
                                 text_color="#111", height=36, corner_radius=8)
    entries[key].pack(side="left", padx=(0, 15))

    fetched_lbls[key] = ctk.CTkLabel(row, text="— — —", font=ctk.CTkFont("Segoe UI", 12),
                                      text_color="#4a4a4a", fg_color="transparent", width=120, anchor="w")
    fetched_lbls[key].pack(side="left", padx=5)

    icon_frame = ctk.CTkFrame(row, fg_color="transparent")
    icon_frame.pack(side="left", padx=6)

    fail_lbls[key] = ctk.CTkLabel(icon_frame, text="✗", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                                   text_color="#CC2222", fg_color="transparent", width=24)
    fail_lbls[key].pack(side="left", padx=2)

    pass_lbls[key] = ctk.CTkLabel(icon_frame, text="✓", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                                   text_color="#888", fg_color="transparent", width=24)
    pass_lbls[key].pack(side="left", padx=2)

# ─── Buttons ─────────────────────────────
btn_frame = ctk.CTkFrame(root, fg_color="transparent")
btn_frame.pack(pady=20)

btn_fetch = ctk.CTkButton(btn_frame, text="Fetch & Compare", font=ctk.CTkFont("Segoe UI", 13, "bold"),
                          fg_color="#5BC954", hover_color="#4CAF50", text_color="black",
                          border_color="#3A9E3A", border_width=2, width=200, height=44, corner_radius=10)
btn_fetch.pack(side="left", padx=10)

btn_clear = ctk.CTkButton(btn_frame, text="Clear", font=ctk.CTkFont("Segoe UI", 13),
                          fg_color="white", hover_color="#E8E8E8", text_color="black",
                          border_color="#BBB", border_width=1, width=130, height=44, corner_radius=10)
btn_clear.pack(side="left", padx=5)

# ─── Result label ────────────────────────
result_label = ctk.CTkLabel(root, text="PASS / FAIL", font=ctk.CTkFont("Segoe UI", 32, "bold"),
                            text_color="black", fg_color="transparent")
result_label.pack(pady=15)

# ─── Device Info Table ───────────────────
table_frame = ctk.CTkFrame(root, fg_color="#D6D6D6", corner_radius=8)
table_frame.pack(padx=20, fill="both", expand=True, pady=(5, 10))

style = ttk.Style()
style.theme_use("clam")
style.configure("T.Treeview", background="#D6D6D6", fieldbackground="#D6D6D6",
                font=("Segoe UI", 10), rowheight=28, borderwidth=0)
style.configure("T.Treeview.Heading", background="#BEBEBE", font=("Segoe UI", 10, "bold"))
style.map("T.Treeview", background=[("selected", "#A8C8E8")])

tree = ttk.Treeview(table_frame, columns=("Property", "Value"), show="headings", height=6, style="T.Treeview")
tree.heading("Property", text="Property")
tree.heading("Value", text="Value")
tree.column("Property", width=250, anchor="w")
tree.column("Value", width=420, anchor="w")
tree.pack(fill="both", expand=True, padx=2, pady=2)

# ─── Get Device Info Button ──────────────
btn_info = ctk.CTkButton(root, text="Get Device Info", font=ctk.CTkFont("Segoe UI", 12),
                         fg_color="white", hover_color="#E8E8E8", text_color="black",
                         border_color="#BBB", border_width=1, width=160, height=38, corner_radius=10)
btn_info.pack(pady=10)

# ───────────────────────────────────────────
#  LOGIC
# ───────────────────────────────────────────

FETCH_FN = {"eid": fetch_eid, "sn": fetch_serial, "imei": fetch_imei}

def set_status(key, passed):
    """Set status icon color"""
    if passed:
        fail_lbls[key].configure(text_color="#AAAAAA")
        pass_lbls[key].configure(text_color="#1E8A1E")
    else:
        fail_lbls[key].configure(text_color="#CC2222")
        pass_lbls[key].configure(text_color="#AAAAAA")

def reset_status(key):
    """Reset status to default"""
    fail_lbls[key].configure(text_color="#CC2222")
    pass_lbls[key].configure(text_color="#888888")

def on_fetch():
    """Fetch and compare"""
    scanned = {key: entries[key].get().strip() for key in entries}

    if not all(scanned.values()):
        messagebox.showwarning("Input Required", "Please fill in all three fields.")
        return

    result_label.configure(text="Fetching…", text_color="#333")
    btn_fetch.configure(state="disabled")
    btn_clear.configure(state="disabled")
    btn_info.configure(state="disabled")

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
            result_label.configure(
                text="✅  PASS" if all_pass else "❌  FAIL",
                text_color="#1A7A1A" if all_pass else "#BB0000"
            ),
            btn_fetch.configure(state="normal"),
            btn_clear.configure(state="normal"),
            btn_info.configure(state="normal")
        ))

    threading.Thread(target=worker, daemon=True).start()

def on_clear():
    """Clear all fields"""
    for key in entries:
        entries[key].delete(0, tk.END)
        fetched_lbls[key].configure(text="— — —")
        reset_status(key)
    result_label.configure(text="PASS / FAIL", text_color="black")
    tree.delete(*tree.get_children())

def on_get_info():
    """Get and display device info"""
    tree.delete(*tree.get_children())
    tree.insert("", "end", values=("Loading…", "Please wait"))
    btn_fetch.configure(state="disabled")
    btn_clear.configure(state="disabled")
    btn_info.configure(state="disabled")

    def worker():
        data = [
            ("Serial No", adb_cmd("get-serialno")),
            ("Brand", adb_cmd("shell", "getprop", "ro.product.brand")),
            ("Model", adb_cmd("shell", "getprop", "ro.product.model")),
            ("Android Version", adb_cmd("shell", "getprop", "ro.build.version.release")),
            ("Build Number", adb_cmd("shell", "getprop", "ro.build.display.id")),
        ]
        root.after(0, lambda: (
            tree.delete(*tree.get_children()),
            [tree.insert("", "end", values=row) for row in data],
            btn_fetch.configure(state="normal"),
            btn_clear.configure(state="normal"),
            btn_info.configure(state="normal")
        ))

    threading.Thread(target=worker, daemon=True).start()

btn_fetch.configure(command=on_fetch)
btn_clear.configure(command=on_clear)
btn_info.configure(command=on_get_info)

root.mainloop()