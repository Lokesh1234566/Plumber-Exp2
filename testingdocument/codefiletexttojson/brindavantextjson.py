import re
import json

input_path = (
    "../txtfile/brindavan_13102 - INVOICE_12.txt"  # Replace with your actual .txt path
)

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

lines = [line.strip() for line in text.splitlines() if line.strip()]


# Helper
def extract(pattern, source, default="", flags=0):
    match = re.search(pattern, source, flags)
    return match.group(1).strip() if match else default


# ---------------------
# Supplier Details
# ---------------------
supplier_details = {
    "name": lines[0],
    "address": ", ".join(lines[1:5]),
    "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
    "state_name": extract(r"State Name\s*:\s*(.+?),", text),
    "state_code": extract(r"Code\s*:\s*(\d+)", text),
    "contact": extract(r"Contact\s*:\s*(.+)", text),
    "email": extract(r"E-Mail\s*:\s*(.+)", text),
}

# ---------------------
# Buyer Details
# ---------------------
# Buyer Details
buyer_block = extract(
    r"Buyer\s*(.*?)GSTIN/UIN", text, default="", flags=re.DOTALL
).strip()
buyer_lines = buyer_block.splitlines()

buyer_details = {
    "name": buyer_lines[0].strip() if buyer_lines else "",
    "address": " ".join(line.strip() for line in buyer_lines if line.strip()),
    "gstin_uin": extract(r"GSTIN/UIN \s*:\s*(\S+)", text),
}


# ---------------------
# Invoice Details
# Invoice Details
# ---------------------
invoice_labels = [
    "BRINDAVAN\\13102",
    "Delivery Note",
    "Supplier's Ref.",
    "Buyer's Order No.",
    "Despatch Document No.",
    "Despatched through",
    "Terms of Delivery",
    "Mode/Terms of Payment",
    "Other Reference(s)",
    "Dated",
    "Delivery Note Date",
    "Destination",
]

# Cleaned keys for internal dictionary use
clean_keys = [
    label.replace(":", "").replace("\\", "").strip() for label in invoice_labels
]
invoice_details = {label: "" for label in clean_keys}

excluded_values = [
    "",  # empty
    "Sl                Description of Goods            HSN/SAC   Part No.    Quantity     Rate     per     Amount",
]

for i in range(len(lines) - 1):
    key = lines[i].strip().replace(":", "").replace("\\", "")
    val = lines[i + 1].strip()

    if key in invoice_details:
        if val not in clean_keys and val not in excluded_values:
            invoice_details[key] = val
        else:
            invoice_details[key] = ""  # next line is not usable

# Rename "BRINDAVAN13102" to "Invoice No"
invoice_details["Invoice No"] = invoice_details.pop("BRINDAVAN13102")

# ---------------------
# Line Items
# Line Items
# ---------------------
line_items = []
item_pattern = re.compile(
    r"^(.+?)\s{2,}(\d{6,8})\s+(\d+)\s+([A-Za-z]+)\s+([\d,]+\.\d{2})\s+([A-Za-z]+)\s+([\d,]+\.\d{2})$"
)

for line in lines:
    match = item_pattern.match(line)
    if match:
        description = match.group(1).strip()
        hsn = match.group(2)
        part_no = match.group(3)
        quantity = f"{match.group(3)} {match.group(4)}"
        rate = match.group(5)
        per = match.group(6)
        amount = match.group(7)

        line_items.append(
            {
                "Description of Goods": description,
                "HSN/SAC": hsn,
                "Part No": part_no,
                "Quantity": quantity,
                "Rate": rate,
                "per": per,
                "Amount": amount,
            }
        )

# ---------------------
# Tax Summary
# ---------------------
tax_summary = {
    "CGST Rate (%)": extract(r"Output CGST @\s*(\d+)%", text),
    "CGST Amount": extract(r"Output CGST @\s*\d+%\s+\d+ %\s+([\d,.]+)", text),
    "SGST Rate (%)": extract(r"Output SGST @\s*(\d+)%", text),
    "SGST Amount": extract(r"Output SGST @\s*\d+%\s+\d+ %\s+([\d,.]+)", text),
}

# Clean empty rates
tax_summary = {k: v if v else "" for k, v in tax_summary.items()}

# ---------------------
# HSN Summary
# ---------------------
hsn_summary = []
hsn_match = re.search(
    r"(\d{6,8})\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+([\d,.]+)", text
)
if hsn_match:
    hsn_summary.append(
        {
            "HSN/SAC": hsn_match.group(1),
            "Taxable Value": hsn_match.group(2),
            "CGST Rate": hsn_match.group(3) + "%",
            "CGST Amount": hsn_match.group(4),
            "SGST Rate": hsn_match.group(5) + "%",
            "SGST Amount": hsn_match.group(6),
            "Total Tax Amount": hsn_match.group(7),
        }
    )

# ---------------------
# Bank Details
# ---------------------
bank_details = {
    "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
    "Account Number": extract(r"A/c No\.\s*:\s*(\d+)", text),
    "Branch & IFS Code": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", text),
}

# ---------------------
# Final Output
# ---------------------
output = {
    "supplier_details": supplier_details,
    "buyer_details": buyer_details,
    "invoice_details": invoice_details,
    "line_items": line_items,
    "tax_summary": tax_summary,
    "hsn_summary": hsn_summary,
    "bank_details": bank_details,
}

# Save to JSON
with open("brindavan_13102 - INVOICE_12.txt.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print("✅ Data extracted and saved to brindavan_invoice_output.json")
