import re
import json

# -------------------------
# Load invoice text
# -------------------------
input_path = "./txtfile/sb_tech_PI_IRILLIC_17032021_03.txt"

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

with open(input_path, "r", encoding="utf-8") as file:
    lines = [line.strip() for line in file.readlines() if line.strip()]

# -------------------------
# Helper function
# -------------------------
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default

# -------------------------
# --- Extract supplier address dynamically ---
# -------------------------
# --- Extract supplier address (first 2 lines only) ---
# -------------------------

address_lines = []
for line in lines:
    clean_line = line.strip()
    if clean_line:
        address_lines.append(clean_line)
    if len(address_lines) == 2:
        break

# Clean and deduplicate
cleaned_address = ', '.join(address_lines)

supplier_details = {
    "name": "",  # explicitly blank
    "address": cleaned_address,
    "gstin_uin": extract(r"GSTIN[:\s]+(\S+)", text),
    "phone": extract(r"PH:\+?([\d\s]+)", text)
}

# -------------------------
# -------------------------
# -------------------------
# Buyer Details (Fix: after "To" block)
buyer_name = ""
buyer_address_lines = []

invoice_keywords = ["Our DC No.", "Your P.O.", "GST", "Invoice No.", "Your DC No.", "Date"]

for i, line in enumerate(lines):
    if line.strip().startswith("To"):
        # Get buyer name (line after 'To')
        name_index = i + 1
        buyer_name = lines[name_index].strip()

        # --- Step 1: Backward address scan ---
        k = name_index - 1
        while k > 0:
            prev_line = lines[k].strip()
            if not prev_line or "To" in prev_line:
                break
            buyer_address_lines.insert(0, prev_line)  # insert at start
            k -= 1

        # --- Step 2: Forward address scan ---
        for j in range(name_index + 1, name_index + 6):
            if j >= len(lines):
                break
            current_line = lines[j].strip()
            if not current_line:
                continue
            if any(keyword in current_line for keyword in invoice_keywords):
                # Cut off the line at the keyword
                for keyword in invoice_keywords:
                    if keyword in current_line:
                        current_line = current_line.split(keyword)[0].strip()
            if current_line:
                buyer_address_lines.append(current_line)
        break

buyer_details = {
    "name": buyer_name,
    "address": ', '.join(buyer_address_lines),
    "gstin_uin": extract(r"Consignee GST:\s*(\S+)", text)
}




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
import re

# Assume `lines` is your list of stripped text lines from the invoice
invoice_details = {
    "Invoice No": "",
    "Invoice Date": "",
    "Our DC No": "",
    "Our DC Date": "",
    "Your DC No": "",
    "Your DC Date": "",
    "PO No": "",
    "PO Date": "",
    "Payment Terms": "",
    "Delivery": ""
}

# Patterns to detect inline content if needed
inline_patterns = {
    "Invoice No": r"Invoice No\.?\s*[:\-]?\s*(\S+)",
    "Invoice Date": r"Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
    "PO No": r"P\.?O\.? No\.?\s*[:\-]?\s*(\S+)",
    "PO Date": r"P\.?O\.? No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
    "Payment Terms": r"Payment Terms\s*[:\-]?\s*(.*)",
    "Delivery": r"Delivery\s*[:\-]?\s*(.*)",
    "Our DC No": r"Our DC No\.?\s*[:\-]?\s*(\S+)",
    "Our DC Date": r"Our DC No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
    "Your DC No": r"Your DC No\.?\s*[:\-]?\s*(\S+)",
    "Your DC Date": r"Your DC No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})"
}

# Helper function to extract via regex
def extract(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

# Join full text for regex-based extraction
full_text = "\n".join(lines)

# Apply regex extraction first (useful for inline values)
for key, pattern in inline_patterns.items():
    invoice_details[key] = extract(pattern, full_text)

# Fallback extraction from line structure (next-line format)
labels = {
    "Invoice No.": "Invoice No",
    "Date": ["Invoice Date", "PO Date", "Our DC Date", "Your DC Date"],
    "Our DC No.": "Our DC No",
    "Your DC No.": "Your DC No",
    "Your P.O. No.": "PO No",
    "Payment Terms": "Payment Terms",
    "Delivery": "Delivery"
}

seen_date_fields = set()

for i in range(len(lines) - 1):
    current = lines[i].strip()
    next_line = lines[i + 1].strip()

    if current in labels:
        keys = labels[current]
        if isinstance(keys, list):
            # Assign to the first missing date key
            for date_key in keys:
                if not invoice_details[date_key] and date_key not in seen_date_fields:
                    invoice_details[date_key] = next_line if next_line.lower() != "date" else ""
                    seen_date_fields.add(date_key)
                    break
        else:
            if not invoice_details[keys]:
                invoice_details[keys] = next_line if next_line.lower() != "date" else ""

# Final cleanup: remove placeholder text like 'Date'
for key, value in invoice_details.items():
    if value.lower() == "date":
        invoice_details[key] = ""

# ✅ Result
# print("invoice_details =", invoice_details)



# -------------------------
# Line Items Extraction
# -------------------------
line_items = []
line_pattern = re.compile(
    r"^\s*(\d+)\s+(.*?)\s+(\d{6,8})\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)",
    re.MULTILINE
)

for match in line_pattern.finditer(text):
    sl_no, desc, hsn, qty, unit_price, amount = match.groups()
    line_items.append({
        "Sl No": sl_no,
        "Description": desc.strip(),
        "HSN/SAC": hsn,
        "Quantity": int(qty),
        "Unit Price": float(unit_price.replace(",", "")),
        "Amount": float(amount.replace(",", ""))
    })

# -------------------------
# Tax Summary
# -------------------------
tax_summary = {
    "CGST 9%": extract(r"CGST\s+9%\s+([\d,]+\.\d{2})", text),
    "SGST 9%": extract(r"SGST\s+9%\s+([\d,]+\.\d{2})", text),
    "IGST 18%": extract(r"IGST\s+18%\s+([\d,]+\.\d{2})", text)
}

# -------------------------
# Totals and Amount in Words
# -------------------------
total_amount = extract(r"TOTAL\s+(\d{5,7}\.\d{2})", text)
amount_chargeable_words = extract(r"TOTAL INVOICE VALUE\s+Rupees\s+(.*?)\s+\d", text)

totals = {
    "Total Amount (before tax)": sum(item["Amount"] for item in line_items),
    "CGST": float(tax_summary["CGST 9%"].replace(",", "")) if tax_summary["CGST 9%"] else 0.0,
    "SGST": float(tax_summary["SGST 9%"].replace(",", "")) if tax_summary["SGST 9%"] else 0.0,
    "IGST": float(tax_summary["IGST 18%"].replace(",", "")) if tax_summary["IGST 18%"] else 0.0,
    "Total Invoice Value": float(total_amount.replace(",", "")) if total_amount else 0.0
}

# -------------------------
# Bank Details (if available)
# -------------------------
bank_details = {
    "Bank Name": extract(r"Bank Name\s*:\s*(.*)", text) or "N/A",
    "A/c No": extract(r"A/c No\.?\s*[:\-]?\s*(\d+)", text) or "N/A",
    "Branch & IFS Code": extract(r"Branch & IFS Code\s*:\s*(.*)", text) or "N/A"
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
    "bank_details": bank_details
}

# -------------------------
# Save as JSON
# -------------------------
with open("sb_tech_PI_IRILLIC_17032021_03.json", "w", encoding="utf-8") as json_file:
    json.dump(output_data, json_file, indent=4)

print("✅ JSON extracted and saved to 'SB_Tech_Invoice.json'")
