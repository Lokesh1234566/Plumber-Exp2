import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./outputfile/A.txt"  # Update to your file path

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
    "name": extract(r"^(INFINITI ENGINEERS PRIVATE LIMITED)", text),
    "address": extract(r"INFINITI ENGINEERS PRIVATE LIMITED\n(.+?\n.+?\n.+?)\n", text).replace("\n", ", "),
    "phone": extract(r"PH:\s*(.+)", text),
    "pan": extract(r"PAN NO:\s*(\S+)", text),
    "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", text),
    "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
    "email": extract(r"E-Mail\s*:\s*(.+)", text)
}

# -------------------------
# Buyer Details
# -------------------------
buyer_name = extract(r"Buyer\s*\n([^\n]+)", text)
buyer_address = extract(rf"Buyer\s*\n{re.escape(buyer_name)}\n(.+\n.+\n.+)", text, "").replace("\n", ", ")
buyer_details = {
    "name": buyer_name,
    "address": buyer_address,
    "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", text),
    "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", text)
}

# -------------------------
# Invoice Details
# -------------------------
invoice_keys = [
    "Invoice No.", "Delivery Note", "Supplier’s Ref.", "Buyer’s Order No.",
    "Despatch Document No.", "Despatched through", "Dated",
    "Mode/Terms of Payment", "Other Reference(s)", "Delivery Note Date",
    "Destination", "Terms of Delivery"
]

invoice_details = {}
for i, line in enumerate(lines):
    if line in invoice_keys:
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        if next_line.strip() in invoice_keys or next_line.strip() == "":
            invoice_details[line.rstrip('.')] = ""
        else:
            invoice_details[line.rstrip('.')] = next_line.strip()

# -------------------------
# -------------------------
# Line Items (block capture version)
# -------------------------
line_items = []
lines = text.splitlines()
i = 0
while i < len(lines):
    line = lines[i].strip()
    if "RENTAL OF LAPTOP" in line:
        try:
            header = lines[i].strip()

            hsn_match = re.search(r"(\d{8})", header)
            hsn = hsn_match.group(1) if hsn_match else ""

            qty_match = re.search(r"(\d+)\s+NOS", header)
            qty = qty_match.group(1) if qty_match else ""

            rate_match = re.search(r"NOS\.\s+([\d,]+\.\d{2})", header)
            rate = rate_match.group(1) if rate_match else ""

            amount_match = re.findall(r"([\d,]+\.\d{2})", header)
            amount = amount_match[-1] if amount_match else ""

            per_match = re.search(r"\b(NOS)\b", header)
            per = per_match.group(1) if per_match else ""

            # Capture full description block (up to 5 lines after "RENTAL OF LAPTOP")
            desc_block_lines = []
            for offset in range(1, 6):
                if i + offset < len(lines):
                    desc_block_lines.append(lines[i + offset].strip())
            full_desc = " ".join(desc_block_lines).strip()

            line_items.append({
                "Description of Goods": full_desc,
                "HSN/SAC": hsn,
                "Quantity": qty,
                "Rate": rate,
                "per": per,
                "Disc. %": "",
                "Amount": amount
            })

            i += 6  # move to next item
        except Exception as e:
            print(f"⚠️ Error parsing item at line {i}: {e}")
            i += 1
    else:
        i += 1


# -------------------------
# Tax Summary
# -------------------------
tax_summary = {
    "SGST Rate (%)": extract(r"SGST\s*@\s*(\d+)%", text),
    "SGST Amount": extract(r"SGST\s*@\s*\d+%\s*\d+\s*%\s*([\d,]+\.\d{2})", text),
    "CGST Rate (%)": extract(r"CGST\s*@\s*(\d+)%", text),
    "CGST Amount": extract(r"CGST\s*@\s*\d+%\s*\d+\s*%\s*([\d,]+\.\d{2})", text)
}

# -------------------------
# Totals
# -------------------------
totals = {
    "Total Quantity": extract(r"Total\s+(\d+)\s+NOS", text),
    "Total Amount": extract(r"Total\s+\d+\s+NOS\.\s+[^\d]*([\d,]+\.\d{2})", text)
}

# -------------------------
# Amount Chargeable (in words)
# -------------------------
amount_chargeable_words = ""
for i, line in enumerate(lines):
    if "Amount Chargeable (in words)" in line:
        amount_chargeable_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
        break

tax_amount_in_words = ""
for i, line in enumerate(lines):
    if "Tax Amount (in words)" in line:
        tax_amount_in_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
        break

# -------------------------
# HSN Tax Summary
# -------------------------
hsn_summary = []

# Try finding each HSN line (one per product/service)
hsn_blocks = re.findall(
    r"(\d{6,8})\s+([\d,]+\.\d{2})\s+([\d.]+)%\s+([\d,]+\.\d{2})\s+([\d.]+)%\s+([\d,]+\.\d{2})",
    text
)

for hsn, taxable_val, cgst_rate, cgst_amt, sgst_rate, sgst_amt in hsn_blocks:
    total_tax_amt = f"{(float(cgst_amt.replace(',', '')) + float(sgst_amt.replace(',', ''))):,.2f}"
    hsn_summary.append({
        "HSN/SAC": hsn,
        "Taxable Value": taxable_val,
        "Central Tax Rate": f"{cgst_rate}%",
        "Central Tax Amount": cgst_amt,
        "State Tax Rate": f"{sgst_rate}%",
        "State Tax Amount": sgst_amt,
        "Total Tax Amount": total_tax_amt
    })
# -------------------------
# -------------------------
# -------------------------
# -------------------------
# -------------------------
# Bank Details (full extraction logic)
# -------------------------

# Extract bank name and account number from the line: BANK OF BARODA (89490200000377)
bank_line = extract(r"Bank Name\s*:\s*(.+)", text)

bank_name = ""
account_number = ""

if bank_line:
    bank_match = re.match(r"(.+?)\s*\((\d{10,20})\)", bank_line)
    if bank_match:
        bank_name, account_number = bank_match.groups()
    else:
        bank_name = bank_line.strip()

# ✅ Extract Branch & IFSC Code from the same line format: Branch & IFS Code : JAYANAGAR, BARB0JAYANG
branch_ifsc_line = extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", text)
branch_ifsc = branch_ifsc_line.strip() if branch_ifsc_line else ""

# Fallback: extract separate Branch and IFSC if that didn’t work
if not branch_ifsc:
    branch = extract(r"Branch\s*:\s*(.+)", text)
    ifsc = extract(r"IFSC\s*:\s*(\S+)", text)
    if branch and ifsc:
        branch_ifsc = f"{branch}, {ifsc}"
    elif ifsc:
        branch_ifsc = ifsc

# Final bank_details dictionary
bank_details = {
    "Bank Name": bank_name.strip(),
    "Account Number": account_number,
    "Branch_IFSC": branch_ifsc
}


# -------------------------
# Final Output JSON
# -------------------------
output_data = {
    "supplier_details": supplier_details,
    "buyer_details": buyer_details,
    "invoice_details": invoice_details,
    "line_items": line_items,
    "tax_summary": tax_summary,
    "totals": totals,
    "amount_chargeable_in_words": amount_chargeable_words,
    "hsn_summary": hsn_summary,
    "bank_details": bank_details
}

# Save to file
output_path = "A.json"
with open(output_path, "w", encoding="utf-8") as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"✅ Invoice data extracted to: {output_path}")
