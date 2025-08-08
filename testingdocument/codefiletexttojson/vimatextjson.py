import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/vima3ya_214 Signed_01.txt"  # Replace with your actual path

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

with open(input_path, "r", encoding="utf-8") as file:
    lines = [line.strip() for line in file.readlines()]

# -------------------------
# Helper function
# -------------------------
def extract(pattern, source, default=''):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default

# -------------------------
# Supplier Details
# -------------------------
supplier_details = {
    "name": lines[0].strip(),
    "address": ', '.join(lines[1:3]).strip(),
    "msme_reg_no": extract(r"MSME REG\.NO\.([A-Z0-9]+)", text),
    "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),", text),
    "state_code": extract(r"Code\s*:\s*(\d+)", text),
    "email": extract(r"E-Mail\s*:\s*(.+)", text),
    "contact": extract(r"Contact\s*:\s*(\S+)", text)
}

# -------------------------
# Buyer & Consignee Details
# -------------------------
def extract_block(start_keyword):
    start = None
    for i, line in enumerate(lines):
        if start_keyword.lower() in line.lower():
            start = i
            break
    if start is not None:
        block = lines[start+1:start+6]
        return block
    return []

buyer_block = extract_block("Buyer (if other than consignee)")
buyer_details = {
    "name": buyer_block[0] if len(buyer_block) > 0 else "",
    "address": ', '.join(buyer_block[1:3]) if len(buyer_block) > 2 else "",
    "gstin_uin": extract(r"GSTIN/UIN \s*:\s*([A-Z0-9]+)", text),
    "pan": extract(r"PAN/IT\s*No\s*:\s*([A-Z0-9]+)", text),
    "state_name": extract(r"State Name\s*:\s*(.*?),", text),
    "state_code": extract(r"Code\s*:\s*(\d+)", text),
    "place_of_supply": extract(r"Place of Supply\s*:\s*(.*)", text)
}

# -------------------------
# Invoice Details
# Define the expected invoice fields in order
invoice_labels = [
    "Invoice No", "Delivery Note", "Supplier’s Ref", "Buyer's Order No",
    "Despatch Document No", "Despatched through", "Bill of Lading/LR-RR No",
    "Terms of Delivery", "Mode/Terms of Payment", "Other Reference(s)",
    "Dated", "Delivery Note Date", "Destination", "Motor Vehicle No"
]

invoice_details = {label: "" for label in invoice_labels}  # initialize with blanks

# Iterate through lines and fill values
for i in range(len(lines) - 1):
    current_line = lines[i].strip().replace(":", "")
    next_line = lines[i + 1].strip()

    # If current line is a known label, take next line as value (unless it's also a label)
    if current_line in invoice_details:
        if next_line not in invoice_labels and next_line != "":
            invoice_details[current_line] = next_line
        else:
            invoice_details[current_line] = ""

# Optional: remove empty values if you prefer (otherwise keep all keys)
# invoice_details = {k: v for k, v in invoice_details.items()}

# -------------------------
# Line Items
# -------------------------
# Line Items (Updated)
# -------------------------

line_items = []
item_pattern = re.compile(
    r"^(\d+)\s+(.*?)\s+(\d{6,8})\s+([\d,.]+)\s+([A-Za-z]+)\s+([\d,.]+)\s+([A-Za-z]+)\s+([\d,.]+)$"
)

for line in lines:
    match = item_pattern.match(line)
    if match:
        line_items.append({
            "Sl No": match.group(1),
            "Description of Goods": match.group(2).strip(),
            "HSN/SAC": match.group(3),
            "Quantity": match.group(4),
            "Qty Unit": match.group(5),
            "Rate": match.group(6),
            "Rate Unit": match.group(7),
            "Amount": match.group(8)
        })


# -------------------------
# Tax Summary
# -------------------------
tax_summary = {
    "CGST Rate (%)": "",
    "CGST Amount": "",
    "SGST Rate (%)": "",
    "SGST Amount": ""
}
for line in lines:
    if 'Output CGST' in line:
        tax_summary["CGST Rate (%)"] = extract(r'CGST\s*@\s*(\d+)%', line)
        tax_summary["CGST Amount"] = extract(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', line)
    elif 'Output SGST' in line:
        tax_summary["SGST Rate (%)"] = extract(r'SGST\s*@\s*(\d+)%', line)
        tax_summary["SGST Amount"] = extract(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', line)

# -------------------------
# HSN Summary
# -------------------------
hsn_summary = []
for line in lines:
    match = re.search(
        r'(\d{6,8})\s+([\d,.]+)\s+(\d+%)\s+([\d,.]+)\s+(\d+%)\s+([\d,.]+)\s+([\d,.]+)', line
    )
    if match:
        hsn_summary.append({
            "HSN/SAC": match.group(1),
            "Taxable Value": match.group(2),
            "CGST Rate": match.group(3),
            "CGST Amount": match.group(4),
            "SGST Rate": match.group(5),
            "SGST Amount": match.group(6),
            "Total Tax Amount": match.group(7)
        })

# -------------------------
# Bank Details
# -------------------------
bank_details = {
    "Bank Name": extract(r"Bank Name\s*:\s*(.+?)(?=\s*A/c No)", text),
    "Account Number": extract(r"A/c No\.?\s*[:\-]?\s*(\d+)", text),
    "Branch": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.*)\s+&", text),
    "IFSC Code": extract(r"&\s*(VIJB\d+)", text)
}

# -------------------------
# Final Output
# -------------------------
output_data = {
    "supplier_details": supplier_details,
    "buyer_details": buyer_details,
    "invoice_details": invoice_details,
    "line_items": line_items,
    "tax_summary": tax_summary,
    "hsn_summary": hsn_summary,
    "bank_details": bank_details
}

# Save to JSON file
with open("vima3ya_214 Signed_01.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print("✅ Extracted data saved to extracted_invoice.json")
