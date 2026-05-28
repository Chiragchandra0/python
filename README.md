# Device Verification Tool - Setup Guide

## Installation

### Required Python Packages
```bash
pip install customtkinter pillow pytesseract pandas openpyxl
```

### Tesseract OCR (for IMEI scanning)
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location (C:\Program Files\Tesseract-OCR)
3. If installed elsewhere, update the path in verification_tool.py

### ADB Path
Update the ADB path in both files:
```python
ADB = r"C:\Users\YOUR_USERNAME\path\to\adb.exe"
```

---

## Files Overview

### 1. **verification_tool.py** (Main Application)
The main GUI window with three tabs:
- **EID Verification**: Scanned EID vs Device EID
- **Serial Number**: Scanned S/N vs Device Serial
- **IMEI Verification**: Scanned IMEI vs Device IMEI (with OCR fallback)
- **Get Info**: Display device properties (Brand, Model, Android Version, etc.)
- **File Menu**: Access Excel Verification

### 2. **excel_verifier.py** (Separate Module)
Opens a new window for bulk device verification against Excel files:
- Import Excel file
- Automatically extracts device properties via ADB
- Matches device Model in Excel
- Compares all fields and shows results

---

## Excel File Format

### Required Columns
The Excel file should have these columns (column order doesn't matter):

| Model | Brand | Android Version | Base Version | Build Number | Security Patch | Serial No | WiFi MAC | Bluetooth MAC | Battery |
|-------|-------|-----------------|--------------|--------------|----------------|-----------|----------|---------------|---------|
| Pixel 6 | Google | 13 | 13 | TP1A.220624.014 | 2024-01-05 | ABC123XYZ | 12:34:56:78:9A:BC | DE:F0:12:34:56:78 | 100 % |
| OnePlus 10 | OnePlus | 12 | 12.1 | OKM1 | 2024-01-01 | XYZ789 | AA:BB:CC:DD:EE:FF | 11:22:33:44:55:66 | 98 % |

### Notes:
- **Column names must match exactly** (case-sensitive)
- Model name is used to find the matching row in Excel
- All other fields are compared with ADB extracted values
- Comparison is case-insensitive

### Example Excel Setup:
```
Save as: device_database.xlsx

Sheet 1:
├─ Model (Primary key for matching)
├─ Brand
├─ Android Version
├─ Base Version
├─ Build Number
├─ Security Patch
├─ Serial No
├─ WiFi MAC
├─ Bluetooth MAC
├─ Battery
```

---

## Usage

### Main Window (verification_tool.py)

1. **EID/S/N/IMEI Verification**
   - Manually scan or enter values in the three input fields
   - Click "Fetch & Compare"
   - System extracts values from connected device via ADB
   - Shows ✓ (green) if match, ✗ (red) if no match
   - Display shows **PASS** if all three match, **FAIL** otherwise

2. **Get Device Info**
   - Click "Get Info" button
   - Displays device properties in table (Brand, Model, Android Version, etc.)

3. **Clear**
   - Clears all input fields and results

### Excel Verification Window (File → Excel Verification)

1. Click **📁 Import Excel** button
2. Select your Excel file (device_database.xlsx)
3. Click **✓ Verify** button
4. System will:
   - Extract Model from connected device
   - Find matching row in Excel by Model
   - Extract remaining device properties
   - Compare each field
   - Display results with ✓ or ✗ for each field
   - Show **MATCH** (green) if all fields match, **NO MATCH** (red) if any field differs

---

## Troubleshooting

### "Device not connected"
- Check if device is connected: `adb devices`
- Enable USB Debugging on the device
- Check if ADB path is correct

### "Could not fetch IMEI"
- OCR may fail on some devices
- Try manual entry approach
- Check Tesseract installation

### "Model not found in Excel"
- Check if device Model name matches exactly in Excel
- Model comparison is case-insensitive but must match format
- Verify Excel file is in correct format

### Excel file won't load
- Ensure file is .xlsx or .xls format
- Close file in Excel before importing
- Check for special characters in file path

---

## Code Structure

### Main Application Flow:
```
verification_tool.py
├── Main GUI Window (740x680)
├── File Menu
│   └── Excel Verification → Opens excel_verifier.ExcelVerifyWindow
└── Three field comparisons (EID, S/N, IMEI)

excel_verifier.py
├── ExcelVerifyWindow Class
├── Import Excel functionality
├── ADB property extraction
└── Field-by-field comparison
```

### Key Functions:

**verification_tool.py:**
- `fetch_eid()` - Extract eUICC EID from device
- `fetch_serial()` - Extract Serial Number
- `fetch_imei()` - Extract IMEI via service call or OCR
- `fetch_device_info()` - Get device properties for info table

**excel_verifier.py:**
- `fetch_properties()` - Extract all device properties at once
- `ExcelVerifyWindow._import_excel()` - Load Excel file
- `ExcelVerifyWindow._verify()` - Compare device properties with Excel row

---

## Tips

1. **Performance**: First time IMEI extraction via OCR takes ~10 seconds
2. **Multiple Devices**: Use Excel verification for bulk checking
3. **Field Matching**: Edit Excel column names to match your requirements
4. **Batch Testing**: Add more fields to Excel as needed

---

## Support

For issues:
1. Check device connection: `adb devices`
2. Verify Excel file format
3. Check ADB path configuration
4. Ensure Tesseract is installed (if using OCR)
