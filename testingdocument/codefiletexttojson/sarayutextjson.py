import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/sarayu_186_07.txt"

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

lines = [line.strip() for line in text.splitlines() if line.strip()]

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
    "name": lines[0],
    "address": ', '.join(lines[1:4]),
    "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code", text),
    "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
    "email": extract(r"E-Mail\s*:\s*(\S+)", text)
}

# -------------------------
# Buyer Details
# -------------------------
buyer_details = {
    "name": "Irillic Pvt. Ltd.",
    "address": ', '.join([
        lines[lines.index("Buyer") + 1],
        lines[lines.index("Buyer") + 2]
    ]),
    "gstin_uin": extract(r"GSTIN/UIN \s*:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code", text),
    "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
    "place_of_supply": extract(r"Place of Supply\s*:\s*(.+)", text),
    "contact_person": extract(r"Contact person\s*:\s*(.+)", text),
    "contact": extract(r"Contact\s*:\s*(\S+)", text)
}

# -------------------------
# Invoice Details
# -------------------------
invoice_labels = [
    "Invoice No.", "Delivery Note", "Supplier’s Ref.", "Buyer’s Order No.",
    "Despatch Document No.", "Despatched through", "Dated",
    "Mode/Terms of Payment", "Other Reference(s)", "Delivery Note Date",
    "Destination", "Terms of Delivery"
]

invoice_details = {label.replace(":", "").replace("’", "'").strip(): "" for label in invoice_labels}

for i in range(len(lines) - 1):
    key = lines[i].strip().replace(":", "").replace("’", "'")
    val = lines[i + 1].strip()
    if key in invoice_details and val not in invoice_labels and not val.startswith("Sl "):
        invoice_details[key] = val

# -------------------------
# Line Items
import re

line_items = []

i = 0
while i < len(lines):
    # Pattern that matches line item start
    match = re.match(
        r"^(\d+)\s+([A-Za-z\s&()\-]+)\s+(\d{6,8})\s+(\d+)\s*%\s+(\d+)\s+([A-Za-z]+)\s+(\d+)\s+([A-Za-z]+)\s+([\d,]+\.\d{2})",
        lines[i]
    )
    if match:
        sl_no = match.group(1)
        desc = match.group(2).strip()
        hsn = match.group(3)
        gst_rate = match.group(4)
        qty = f"{match.group(5)} {match.group(6)}"
        rate = match.group(7)
        per = match.group(8)
        amount = match.group(9)

        # Check for description continuation on next line
        if i + 1 < len(lines) and not lines[i + 1].startswith(tuple("1234567890")):
            desc += " " + lines[i + 1].strip()
            i += 1

        line_items.append({
            "Sl No": sl_no,
            "Description of Goods": desc,
            "HSN/SAC": hsn,
            "GST Rate": gst_rate,
            "Quantity": qty,
            "Rate": rate,
            "per": per,
            "Amount": amount
        })
    i += 1


# -------------------------
# Tax Summary
# -------------------------
tax_summary = {}
cgst_line = re.search(r"CGST\s+([\d,.]+)", text)
sgst_line = re.search(r"SGST\s+([\d,.]+)", text)
tax_summary["CGST Amount"] = cgst_line.group(1) if cgst_line else ""
tax_summary["SGST Amount"] = sgst_line.group(1) if sgst_line else ""
# tax_summary["CGST Rate (%)"] = extract(r"48201010\s+350\.00\s+(\d+%)", text)
# tax_summary["SGST Rate (%)"] = extract(r"39230000\s+525\.00\s+(\d+%)", text)

# -------------------------
# HSN Summary
# -------------------------
hsn_summary = []
hsn_pattern = re.compile(r"(\d{6,8})\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+([\d,.]+)")
matches = hsn_pattern.findall(text)
for match in matches:
    hsn_summary.append({
        "HSN/SAC": match[0],
        "Taxable Value": match[1],
        "Central Tax Rate": match[2] + "%",
        "Central Tax Amount": match[3],
        "State Tax Rate": match[4] + "%",
        "State Tax Amount": match[5],
        "Total Tax Amount": match[6]
    })

# -------------------------
# Bank Details
# -------------------------
bank_details = {
    "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
    "Account Number": extract(r"A/c No\.?\s*:\s*(\d+)", text),
    "Branch & IFSC": extract(r"Branch & IFS Code\s*:\s*(.+)", text)
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

# Save JSON
with open("sarayu_186_07.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print("✅ Extracted JSON saved to sarayu_invoice_output.json")
