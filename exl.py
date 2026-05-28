"""
Excel Device Verification Module
Compares ADB-extracted device properties with Excel file data
"""

import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd

ADB = r"C:\Users\Chirag\Desktop\btp\eid\platform-tools-latest-windows\platform-tools\adb.exe"

# ───────────────────────────────────────────
#  ADB HELPERS
# ───────────────────────────────────────────

def adb(*args):
    try:
        return subprocess.check_output([ADB, *args], stderr=subprocess.DEVNULL, timeout=12).decode().strip()
    except:
        return ""

# ───────────────────────────────────────────
#  FETCH DEVICE PROPERTIES
# ───────────────────────────────────────────

def fetch_properties():
    """Extract device properties from ADB"""
    props = {
        "Model": adb("shell", "getprop", "ro.product.model"),
        "Brand": adb("shell", "getprop", "ro.product.brand"),
        "Android Version": adb("shell", "getprop", "ro.build.version.release"),
        "Base Version": adb("shell", "getprop", "ro.build.version.base_os"),
        "Build Number": adb("shell", "getprop", "ro.build.display.id"),
        "Security Patch": adb("shell", "getprop", "ro.build.version.security_patch"),
        "Serial No": adb("get-serialno"),
        "WiFi MAC": _get_wifi_mac(),
        "Bluetooth MAC": adb("shell", "settings", "get", "secure", "bluetooth_address"),
        "Battery": _get_battery(),
    }
    return props

def _get_wifi_mac():
    for line in adb("shell", "ip", "addr", "show", "wlan0").splitlines():
        if "link/ether" in line:
            return line.split()[1]
    return "N/A"

def _get_battery():
    for line in adb("shell", "dumpsys", "battery").splitlines():
        if "level:" in line:
            return line.split(":")[-1].strip() + " %"
    return "N/A"

# ───────────────────────────────────────────
#  EXCEL VERIFICATION WINDOW
# ───────────────────────────────────────────

class ExcelVerifyWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Excel Device Verification")
        self.geometry("900x650")
        self.resizable(False, False)
        self.configure(fg_color="#6B9DC2")

        self.excel_file = None
        self.excel_data = None

        self._build()

    def _build(self):
        # ── Title ────────────────────────────────────
        ctk.CTkLabel(self, text="Excel Device Verification", font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color="white", fg_color="transparent").pack(pady=(16, 10))

        # ── Button row ───────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=10, fill="x")

        self.btn_import = ctk.CTkButton(btn_frame, text="📁 Import Excel", font=ctk.CTkFont("Segoe UI", 12),
                                        fg_color="white", hover_color="#E8E8E8", text_color="black",
                                        border_color="#BBB", border_width=1, width=140, height=38, corner_radius=8,
                                        command=self._import_excel)
        self.btn_import.pack(side="left", padx=8)

        self.btn_verify = ctk.CTkButton(btn_frame, text="✓ Verify", font=ctk.CTkFont("Segoe UI", 12),
                                        fg_color="#5BC954", hover_color="#4CAF50", text_color="black",
                                        border_color="#3A9E3A", border_width=2, width=140, height=38, corner_radius=8,
                                        command=self._verify)
        self.btn_verify.pack(side="left", padx=8)

        self.file_label = ctk.CTkLabel(btn_frame, text="No file selected", font=ctk.CTkFont("Segoe UI", 11),
                                       text_color="#FFF", fg_color="transparent")
        self.file_label.pack(side="left", padx=20)

        # ── Result label ─────────────────────────────
        self.result_lbl = ctk.CTkLabel(self, text="MATCH / NO MATCH", font=ctk.CTkFont("Segoe UI", 28, "bold"),
                                       text_color="black", fg_color="transparent")
        self.result_lbl.pack(pady=10)

        # ── Comparison table ─────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color="#D6D6D6", corner_radius=8)
        table_frame.pack(padx=20, fill="both", expand=True, pady=(8, 12))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("E.Treeview", background="#D6D6D6", fieldbackground="#D6D6D6",
                        font=("Segoe UI", 10), rowheight=28, borderwidth=0)
        style.configure("E.Treeview.Heading", background="#BEBEBE", font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("E.Treeview", background=[("selected", "#A8C8E8")])

        self.tree = ttk.Treeview(table_frame, columns=("Field", "ADB Value", "Excel Value", "Status"),
                                 show="headings", height=16, style="E.Treeview")
        self.tree.heading("Field", text="Field")
        self.tree.heading("ADB Value", text="ADB Value")
        self.tree.heading("Excel Value", text="Excel Value")
        self.tree.heading("Status", text="Match")
        self.tree.column("Field", width=140, anchor="w")
        self.tree.column("ADB Value", width=220, anchor="w")
        self.tree.column("Excel Value", width=220, anchor="w")
        self.tree.column("Status", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

    # ──────────────────────────────────────────
    #  IMPORT EXCEL
    # ──────────────────────────────────────────

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
            messagebox.showerror("Error", f"Failed to load Excel file:\n{str(e)}")

    # ──────────────────────────────────────────
    #  VERIFY
    # ──────────────────────────────────────────

    def _verify(self):
        if self.excel_data is None:
            messagebox.showwarning("No File", "Please import an Excel file first.")
            return

        self.result_lbl.configure(text="Verifying…", text_color="#333")
        self.btn_verify.configure(state="disabled")
        self.btn_import.configure(state="disabled")

        def worker():
            # Extract ADB properties
            adb_props = fetch_properties()
            model = adb_props.get("Model", "").strip()

            if not model:
                self.after(0, lambda: messagebox.showerror("Error", "Could not fetch Model from device."))
                self.after(0, lambda: self._reset_buttons())
                return

            # Find matching row in Excel by Model
            matching_row = None
            for idx, row in self.excel_data.iterrows():
                if str(row.get("Model", "")).strip().upper() == model.upper():
                    matching_row = row
                    break

            if matching_row is None:
                self.after(0, lambda: messagebox.showwarning(
                    "Not Found", f"Model '{model}' not found in Excel file."
                ))
                self.after(0, lambda: self._reset_buttons())
                return

            # Compare each field
            results = []
            matches_count = 0
            for field, adb_val in adb_props.items():
                excel_val = str(matching_row.get(field, "N/A")).strip()
                adb_val = str(adb_val).strip()
                match = adb_val.upper() == excel_val.upper()
                status = "✓" if match else "✗"
                results.append((field, adb_val, excel_val, status))
                if match:
                    matches_count += 1

            # Update UI
            all_match = matches_count == len(results)
            self.after(0, lambda: (
                self.tree.delete(*self.tree.get_children()),
                [self.tree.insert("", "end", values=r) for r in results],
                self.result_lbl.configure(
                    text="✅  MATCH" if all_match else "❌  NO MATCH",
                    text_color="#1A7A1A" if all_match else "#BB0000"
                ),
                self._reset_buttons()
            ))

        threading.Thread(target=worker, daemon=True).start()

    def _reset_buttons(self):
        self.btn_verify.configure(state="normal")
        self.btn_import.configure(state="normal")