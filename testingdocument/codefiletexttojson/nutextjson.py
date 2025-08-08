import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/nu_enterprises_Irillic Sep-20_10.txt"

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

lines = [line.strip() for line in text.splitlines() if line.strip()]

# -------------------------
# Helper extract function
# -------------------------
def extract(pattern, source, group=1, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(group).strip() if match else default

# -------------------------
# Supplier Details
# -------------------------
supplier_details = {
    "name": extract(r"TAX INVOICE\s+(.+)", text),
    "address": extract(r"TAX INVOICE\s+.+\n(.+)", text),
    "pan": extract(r"PAN\s*:\s*(\S+)", text),
    "gstin": extract(r"GSTIN\s*(No)?\s*[:\-]?\s*(\S+)", text, group=2),
    "state": extract(r"STATE\s*-\s*(\w+)", text),
    "month": extract(r"MONTH\s*-\s*(\w+\s+\d{4})", text)
}

# -------------------------
# Buyer Details
# -------------------------
buyer_details = {
    "name": extract(r"NAME\s*:\s*(.+)", text),
    "address": extract(r"NAME\s*:.+\n(.+)", text),
    "gstin": extract(r"GSTIN NO[:\-]*\s*(\S+)", text)
}

# -------------------------
# Invoice Details
# -------------------------
invoice_details = {
    "invoice_number": extract(r"INVOICE NUMBER\s*[:\-]*\s*(\d+)", text),
    "date": extract(r"DATE\s*[:\-]*\s*(\d{2}/\d{2}/\d{4})", text),
    "period": extract(r"Period\s*[:\-]*\s*([^\n]+)", text)
}

# -------------------------
# Line Items
# -------------------------
line_items = []
item_pattern = re.compile(
    r"(\d{2}\.\d{2}\.\d{4})\s+(\d+)\s+([\w\s]+?)\s+(?:\S+)?\s+(\d+kg|\d+gms|\d+)\s+(\d+)\s+([\d,]+\.\d{2})"
)

for match in item_pattern.finditer(text):
    date, awb, dest, weight, quantity, amount = match.groups()
    line_items.append({
        "Date": date,
        "AWB No": awb,
        "Destination": dest.strip(),
        "Weight": weight,
        "Quantity": quantity,
        "Amount": amount
    })

# -------------------------
# Tax Summary
# -------------------------
tax_summary = {
    "SAC Code": extract(r"SAC\s*CODE\s*[:\-]*\s*(\d+)", text),
    "Taxable Amount": extract(r"TAXABLE AMOUNT\s+([\d,]+\.\d{2})", text),
    "CGST %": extract(r"CGST AMOUNT\s*(\d+)%", text),
    "CGST Amount": extract(r"CGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
    "SGST %": extract(r"SGST AMOUNT\s*(\d+)%", text),
    "SGST Amount": extract(r"SGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
    "IGST %": extract(r"IGST AMOUNT\s*(\d+)%", text),
    "IGST Amount": extract(r"IGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
    "Fuel Charges": extract(r"FUEL CHARGERS\s*\d+%\s*([\d,]+\.\d{2})", text),
    "Round Off": extract(r"ROUND OFF\s*([\d,]+\.\d{2})", text)
}

# -------------------------
# Totals
# -------------------------
totals = {
    "Total Amount": extract(r"TOTAL AMOUNT\s*([\d,]+\.\d{2})", text),
    "Invoice Amount": extract(r"INVOICE AMOUNT\s*\n([\d,]+\.\d{2})", text),
    "Total Consignment": extract(r"Total Consignment\s*[:\-]*\s*(\d+)", text)
}

# -------------------------
# Amount in Words
# -------------------------
amount_in_words = extract(r"Amount In words\s*[:-]\s*(.+)", text)

# -------------------------
# Final JSON Output
# -------------------------
output_data = {
    "supplier_details": supplier_details,
    "buyer_details": buyer_details,
    "invoice_details": invoice_details,
    "line_items": line_items,
    "tax_summary": tax_summary,
    "totals": totals,
    "amount_in_words": amount_in_words
}

# -------------------------
# Save to JSON
# -------------------------
with open("nu_enterprises_Irillic Sep-20_10.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print("✅ JSON extracted and saved to 'A_output.json'")
