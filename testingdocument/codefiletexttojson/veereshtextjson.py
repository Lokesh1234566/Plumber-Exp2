import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/veeresh_bill 4_08.txt"  # Replace with your actual .txt path

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

lines = [line.strip() for line in text.splitlines() if line.strip()]

# -------------------------
# Helper
# -------------------------
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default

# -------------------------
# Supplier Details
# -------------------------
supplier_details = {
    "name": lines[0],
    "address": ', '.join(lines[1:3]),
    "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),", text),
    "state_code": extract(r"Code\s*:\s*(\d+)", text),
    "contact": extract(r"Contact\s*:\s*(.+)", text)
}

# -------------------------
# -------------------------
# Buyer Details (Fixed)
# -------------------------
buyer_details = {}
for i, line in enumerate(lines):
    if line.lower() == "customer":
        name = lines[i + 1]
        address = lines[i + 2]
        gstin = ""
        state_name = ""
        state_code = ""

        for j in range(i + 3, min(i + 8, len(lines))):
            if "GSTIN/UIN" in lines[j]:
                gstin = extract(r"GSTIN/UIN\s*:\s*(\S+)", lines[j])
            if "State Name" in lines[j]:
                state_name = extract(r"State Name\s*:\s*(.+?),", lines[j])
                state_code = extract(r"Code\s*:\s*(\d+)", lines[j])

        buyer_details = {
            "name": name,
            "address": address,
            "gstin_uin": gstin,
            "state_name": state_name,
            "state_code": state_code
        }
        break


# -------------------------
# -------------------------
# Invoice Details (Exact logic: current line = key, next line = value)
# -------------------------

invoice_keys = [
    "Invoice No.",
    "Delivery Note",
    "Supplier’s Ref.",
    "Buyer’s Order No.",
    "Despatch Document No.",
    "Despatched through",
    "Dated",
    "Mode/Terms of Payment",
    "Other Reference(s)",
    "Delivery Note Date",
    "Destination",
    "Terms of Delivery"
]

# Clean all keys to remove dots/apostrophes for final JSON
invoice_details = {key.replace("’", "'").replace(".", "").strip(): "" for key in invoice_keys}

# Loop through all lines, checking for exact matches
for i in range(len(lines) - 1):
    current_line = lines[i].strip()
    next_line = lines[i + 1].strip()

    for raw_key in invoice_keys:
        cleaned_key = raw_key.replace("’", "'").replace(".", "").strip()

        # Exact match — line is a key
        if current_line == raw_key:
            # Assign next line as value (if it’s not another key or header)
            if next_line not in invoice_keys and not next_line.startswith("Sl "):
                invoice_details[cleaned_key] = next_line
            else:
                invoice_details[cleaned_key] = ""
# -------------------------
# -------------------------
# -------------------------
# Invoice Details (Handles duplicate keys, picks first occurrence only)
# -------------------------

invoice_keys = [
    "Invoice No.",
    "Delivery Note",
    "Supplier’s Ref.",
    "Buyer’s Order No.",
    "Despatch Document No.",
    "Despatched through",
    "Dated",
    "Mode/Terms of Payment",
    "Other Reference(s)",
    "Delivery Note Date",
    "Destination",
    "Terms of Delivery"
]

# Normalize keys for JSON output
invoice_details = {key.replace("’", "'").replace(".", "").strip(): "" for key in invoice_keys}

# Keep track of which keys we've already set
seen_keys = set()

# Loop through lines
i = 0
while i < len(lines) - 1:
    current_line = lines[i].strip()
    next_line = lines[i + 1].strip()

    for raw_key in invoice_keys:
        cleaned_key = raw_key.replace("’", "'").replace(".", "").strip()

        # Skip if we've already set this key
        if cleaned_key in seen_keys:
            continue

        # Match current line exactly to raw_key
        if current_line == raw_key:
            if next_line not in invoice_keys and not next_line.startswith("Sl "):
                invoice_details[cleaned_key] = next_line
            else:
                invoice_details[cleaned_key] = ""
            seen_keys.add(cleaned_key)
            break

    i += 1


# Line Items
# -------------------------
# Line Items (Fixed Quantity to include number + unit)
# -------------------------

import re

line_items = []
item_pattern = re.compile(
    r"^(\d+)\s+(.*?)\s{2,}(\d+)\s+([A-Z]+)\s+([\d,]+\.\d{2})\s+[A-Z]+\s+([\d,]+\.\d{2})$"
)

for i in range(len(lines)):
    line = lines[i].strip()
    match = item_pattern.match(line)

    if match:
        sl_no = match.group(1)
        description = match.group(2)
        quantity_number = match.group(3)
        quantity_unit = match.group(4)
        rate = match.group(5)
        amount = match.group(6)

        line_items.append({
            "Sl No": sl_no,
            "Particulars": description,
            "HSN/SAC": "",  # HSN not available in this line
            "Quantity": f"{quantity_number} {quantity_unit}",
            "Rate": rate,
            "per": quantity_unit,
            "Amount": amount
        })


# -------------------------
# Tax Summary
# -------------------------
# Tax Summary (Robust - extract from HSN block)
# -------------------------

tax_summary = {
    "CGST Rate (%)": "",
    "CGST Amount": "",
    "SGST Rate (%)": "",
    "SGST Amount": ""
}

# Find the HSN block that contains rates and amounts
for line in lines:
    if re.search(r'\d{1,3}(,\d{3})*\.\d{2}.*\d+%\s+\d{1,3}(,\d{3})*\.\d{2}.*\d+%\s+\d{1,3}(,\d{3})*\.\d{2}', line):
        # Example: 15,220.40   9%   1,369.84  9%  1,369.84  2,739.68
        match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d+)%\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d+)%\s+(\d{1,3}(?:,\d{3})*\.\d{2})', line)
        if match:
            tax_summary["CGST Rate (%)"] = match.group(2)
            tax_summary["CGST Amount"] = match.group(3)
            tax_summary["SGST Rate (%)"] = match.group(4)
            tax_summary["SGST Amount"] = match.group(5)
            break  # we only need one valid line


# -------------------------

# -------------------------
# HSN Summary
# -------------------------

hsn_summary = []

for line in lines:
    line = line.strip()

    # Match lines like:
    # 15,220.40   9%   1,369.84  9%  1,369.84  2,739.68
    match = re.search(
        r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+'        # Taxable Value
        r'(\d+%)\s+'                             # CGST Rate
        r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+'        # CGST Amount
        r'(\d+%)\s+'                             # SGST Rate
        r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+'        # SGST Amount
        r'(\d{1,3}(?:,\d{3})*\.\d{2})',          # Total Tax Amount
        line
    )

    if match:
        hsn_summary.append({
            "HSN/SAC": "",  # Not present in your example
            "Taxable Value": match.group(1),
            "CGST Rate": match.group(2),
            "CGST Amount": match.group(3),
            "SGST Rate": match.group(4),
            "SGST Amount": match.group(5),
            "Total Tax Amount": match.group(6)
        })

# Totals
# -------------------------
total_qty = extract(r"Total\s+(\d+\s+[A-Z]+)", text)
total_amount = extract(r"Total.*?([\d,]+\.\d{2})", text)

totals = {
    "Total Quantity": total_qty,
    "Total Amount": total_amount
}

# -------------------------
# Amount in Words
# -------------------------
amount_chargeable_words = ""
for i, line in enumerate(lines):
    if "Amount Chargeable (in words)" in line:
        amount_chargeable_words = lines[i + 1].strip()
        break

# -------------------------
# -------------------------
# Bank Details
# -------------------------

bank_details = {
    "Bank Name": "",
    "Branch": "",
    "IFSC Code": "",
    "Account Number": ""
}

for line in lines:
    line = line.strip()

    if re.search(r'\bBank Name\b', line, re.IGNORECASE):
        bank_details["Bank Name"] = extract(r'Bank Name\s*:\s*(.*)', line)
    elif re.search(r'\bBank\b', line, re.IGNORECASE) and bank_details["Bank Name"] == "":
        bank_details["Bank Name"] = extract(r'Bank\s*:\s*(.*)', line)

    if re.search(r'IFSC\s*Code', line, re.IGNORECASE):
        bank_details["IFSC Code"] = extract(r'IFSC\s*Code\s*[:\-]?\s*(\S+)', line)

    if re.search(r'Branch', line, re.IGNORECASE):
        if "Branch & IFSC" in line:
            bank_details["Branch"] = extract(r'Branch\s*&\s*IFSC\s*Code\s*:\s*(.*?)\s+\S+$', line)
        else:
            bank_details["Branch"] = extract(r'Branch\s*:\s*(.*)', line)

    if re.search(r'A/c\s*No', line, re.IGNORECASE):
        bank_details["Account Number"] = extract(r'A/c\s*No\.?\s*[:\-]?\s*(\d+)', line)
    elif re.search(r'Account\s*No', line, re.IGNORECASE):
        bank_details["Account Number"] = extract(r'Account\s*No\.?\s*[:\-]?\s*(\d+)', line)

# Final JSON
# -------------------------
output_data = {
    "supplier_details": supplier_details,
    "buyer_details": buyer_details,
    "invoice_details": invoice_details,
    "line_items": line_items,
    "tax_summary": tax_summary,
    "hsn_summary":hsn_summary,
    "totals": totals,
    "amount_chargeable_in_words": amount_chargeable_words,
    "bank_details":bank_details
}

# -------------------------
# Save Output
# -------------------------
output_path = "veeresh_bill 4_08.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print(f"✅ JSON saved to: {output_path}")
