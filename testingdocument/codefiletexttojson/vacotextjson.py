import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/vaco_Inv 453 irrilic Invoice_10.txt"

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
# -------------------------
# -------------------------
# Supplier Details (Reliable Fix)
# -------------------------
supplier_details = {
    "name": "",
    "address": "",
    "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", text),
    "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
    "email": extract(r"E-Mail\s*:\s*(.+)", text)
}

# Find the index of the line with GSTIN/UIN
gstin_index = next((i for i, line in enumerate(lines) if "GSTIN/UIN" in line), None)

if gstin_index is not None:
    # Take the 6 lines above GSTIN
    block = lines[max(0, gstin_index - 6):gstin_index]
    block = [line.strip() for line in block if line.strip()]

    # Search for name in the block
    name_candidates = [line for line in block if re.search(r"(Vasanth|Vaco|and Co|Chartered)", line, re.IGNORECASE)]
    if name_candidates:
        supplier_details["name"] = name_candidates[0]

        # All lines after name are address
        name_index = block.index(name_candidates[0])
        address_lines = block[name_index + 1:]
        supplier_details["address"] = ', '.join(address_lines).strip()



# -------------------------
# Buyer Details
# -------------------------
buyer_details = {
    "name": extract(r"Buyer\s*\n([^\n]+)", text),
    "address": extract(r"Buyer\s*\n[^\n]+\n(.+\n.+\n.+)", text).replace('\n', ', '),
    "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", text),
    "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", text)
}

# -------------------------
# -------------------------
# Invoice Details (Robust + Simple: line contains key, next line is value)
# -------------------------

invoice_keys = [
    "Invoice No.",
    "Delivery Note",
    "Supplier's Ref.",
    "Buyer's Order No.",
    "Despatch Document No.",
    "Despatched through",
    "Dated",
    "Mode/Terms of Payment",
    "Other Reference(s)",
    "Delivery Note Date",
    "Destination",
    "Terms of Delivery"
]

# Initialize cleaned keys dictionary
invoice_details = {key.replace(".", "").strip(): "" for key in invoice_keys}

# Go line by line and check if the key is in the line, then take the next line as value
for i in range(len(lines) - 1):
    current_line = lines[i].strip()
    next_line = lines[i + 1].strip()

    for key in invoice_keys:
        clean_key = key.replace(".", "").strip()

        # Match if the key is in the current line (not exact match)
        if key in current_line and invoice_details[clean_key] == "":
            invoice_details[clean_key] = next_line if next_line else ""




# -------------------------
# -------------------------
# Line Items (Exclude CGST/SGST and support multi-line description)
# -------------------------
line_items = []
item_pattern = re.compile(
    r"^(\d+)\s+(.*?)\s{2,}(\d{6,8})?\s{2,}([\d,]+\.\d{2})$"
)

i = 0
while i < len(lines):
    match = item_pattern.match(lines[i])
    if match:
        sl_no = match.group(1)
        description = match.group(2).strip()
        hsn_sac = match.group(3) or ""
        amount = match.group(4)

        # Filter out tax lines like CGST/SGST
        if re.search(r"(CGST|SGST|IGST)", description, re.IGNORECASE):
            i += 1
            continue

        # Collect full multi-line description
        full_desc = [description]
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if (
                item_pattern.match(lines[j]) or
                next_line.startswith("Total") or
                re.match(r"^\d+\s+(CGST|SGST|IGST)", next_line)
            ):
                break
            if next_line:
                full_desc.append(next_line)
            j += 1

        line_items.append({
            "Sl No": sl_no,
            "Particulars": " ".join(full_desc),
            "HSN/SAC": hsn_sac,
            "Rate": "",
            "per": "",
            "Amount": amount
        })

        i = j
    else:
        i += 1


# -------------------------
# -------------------------
# Tax Summary (Flexible fix)
# -------------------------
tax_summary = {
    "CGST Rate (%)": "",
    "CGST Amount": "",
    "SGST Rate (%)": "",
    "SGST Amount": ""
}

for line in lines:
    if 'CGST' in line:
        tax_summary["CGST Rate (%)"] = extract(r"CGST\s+(\d+)\s*%", line)
        tax_summary["CGST Amount"] = extract(r"(\d{1,3}(?:,\d{3})*\.\d{2})", line)
    elif 'SGST' in line:
        tax_summary["SGST Rate (%)"] = extract(r"SGST\s+(\d+)\s*%", line)
        tax_summary["SGST Amount"] = extract(r"(\d{1,3}(?:,\d{3})*\.\d{2})", line)


# -------------------------
# Totals
# -------------------------
totals = {
    "Total Amount": extract(r"Total\s+₹?\s*([\d,]+\.\d{2})", text)
}

# -------------------------
# Amounts in Words
# -------------------------
amount_chargeable_words = ""
for i, line in enumerate(lines):
    if "Amount Chargeable (in words)" in line:
        amount_chargeable_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
        break

# -------------------------
# Bank Details
# -------------------------
bank_details = {
    "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
    "Account Number": extract(r"A/c\s*No\.?\s*:\s*(\d+)", text),
    "Branch_IFSC": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", text)
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
    "totals": totals,
    "amount_chargeable_in_words": amount_chargeable_words,
    "hsn_summary": [],  # optional for this invoice
    "bank_details": bank_details
}

# Save to file
output_json_path = "vaco_Inv_453_irrilic_Invoice_10.json"
with open(output_json_path, "w", encoding="utf-8") as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"✅ JSON extracted and saved to '{output_json_path}'")
