import json
import os
import re

# --------------------------------------------
# INPUT FILE PATHS
# --------------------------------------------
input_json_path = '../arrayjson/sb_tech_1.json'
input_md_path = '../mdfile/sb_tech_1.md'
output_folder = '../keyvalueMainjsonSBtech'

# --------------------------------------------
# LOAD JSON FILE
# --------------------------------------------
with open(input_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

result = {}

# --------------------------------------------
# EXTRACT COMPANY INFO (Buyer)
# --------------------------------------------
header_block = data[0]["tables"][0][0][0]
lines = header_block.split('\n')

company_lines = []
is_buyer = False
for line in lines:
    if line.strip().startswith("Buyer"):
        is_buyer = True
        continue
    if is_buyer:
        break
    company_lines.append(line.strip())

for line in company_lines:
    key, value = None, None
    if ':' in line:
        key, value = line.split(':', 1)
    elif ' : ' in line:
        key, value = line.split(' : ', 1)
    if key and value:
        result[key.strip()] = value.strip()
    elif line:
        result.setdefault("Company Info", []).append(line)

result["Company Info"] = "\n".join(result["Company Info"])

# --------------------------------------------
# EXTRACT TABLE METADATA
# --------------------------------------------
table = data[0]["tables"][0]

def safe_extract(row_idx, col_idx):
    try:
        cell = table[row_idx][col_idx]
        return cell.strip() if cell else ""
    except IndexError:
        return ""

result["Invoice No"] = safe_extract(0, 4)
result["Date"] = safe_extract(0, 6)
result["Our DC No."] = safe_extract(2, 4)
result["Our DC Date"] = safe_extract(2, 6)
result["Your DC No."] = safe_extract(3, 4)
result["Your DC Date"] = safe_extract(3, 6)
result["Your P.O. No."] = safe_extract(4, 4)
result["Your P.O. Date."] = safe_extract(4, 6)
result["Consignee GST"] = safe_extract(5, 0)
result["Payment Terms"] = safe_extract(5, 3)

# --------------------------------------------
# EXTRACT ITEM TABLE
# --------------------------------------------
items = []
taxes = []
total_amount = ""
rows = table
i = 6

while i < len(rows):
    row = rows[i]
    if row and row[0].strip().isdigit():
        items.append({
            "Sl": row[0].strip(),
            "Description": row[1].strip() if len(row) > 1 else "",
            "HSN/SAC": row[3].strip() if len(row) > 3 else "",
            "Rate": row[5].strip() if len(row) > 5 else "",
            "Amount": row[6].strip() if len(row) > 6 else ""
        })
    elif any("Total" in str(cell).upper() for cell in row):
        total_amount = row[-1].strip()
    elif any(t in str(row[0]).lower() for t in ["cgst", "sgst", "igst"]):
        taxes.append({
            "Type": row[0].strip(),
            "Rate": "",
            "Amount": row[-1].strip()
        })
    elif any("INVOICE VALUE" in str(cell).upper() for cell in row):
        total_amount = row[-1].strip()
        for cell in row:
            if "Rupees" in cell:
                result["Amount Chargeable (in words)"] = cell.strip()
    i += 1

if items:
    result["Items"] = items
if taxes:
    result["Taxes"] = taxes
if total_amount:
    result["Total Amount"] = total_amount

# --------------------------------------------
# PARSE MARKDOWN FOR SELLER INFO, GSTIN, FOOTER
# --------------------------------------------
with open(input_md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

md_lines = [line.strip() for line in md_content.strip().splitlines() if line.strip()]

# Seller Info
for idx, line in enumerate(md_lines):
    if line.startswith("##") and not line.lower().startswith("## tax invoice"):
        seller_name = line.lstrip('#').strip()
        address_lines = []
        for j in range(idx + 1, len(md_lines)):
            if md_lines[j].startswith("##") or "GSTIN" in md_lines[j]:
                break
            address_lines.append(md_lines[j])
        result["Seller Info"] = f"{seller_name}, " + ", ".join(address_lines)
        break

# GSTIN
gstin_match = re.search(r'\b(29[A-Z0-9]{13})\b', md_content)
if gstin_match:
    result["Seller GSTIN"] = gstin_match.group(1)

# Footer
footer_line = next((line for line in reversed(md_lines) if line.lower().startswith("for ")), None)
if footer_line:
    result["Authorised Signatory"] = footer_line.replace("For", "").strip()

# --------------------------------------------
# Extract Bank Details
# --------------------------------------------
bank_lines = []
for line in md_lines:
    if re.search(r'\b(A/C|Account|Bank|IFSC|Branch)\b', line, re.IGNORECASE):
        bank_lines.append(line)
if bank_lines:
    result["Bank Details"] = "\n".join(bank_lines)

# --------------------------------------------
# Extract Contact Info (from Seller section)
# --------------------------------------------
contact_info = []
for line in result.get("Seller Info", "").split(','):
    if re.search(r'[\d\+]{5,}', line) or "@" in line:
        contact_info.append(line.strip())
if contact_info:
    result["Contact Info"] = ", ".join(contact_info)

# --------------------------------------------
# Extract Terms & Conditions (from bottom of md)
# --------------------------------------------
terms_keywords = ["interest", "payment", "discrepancy", "acceptance", "rejection", "report", "terms"]
terms_lines = []
for line in md_lines[-15:]:
    if any(k in line.lower() for k in terms_keywords):
        terms_lines.append(line)
if terms_lines:
    result["Terms & Conditions"] = "\n".join(terms_lines)

# --------------------------------------------
# Clean & Save JSON
# --------------------------------------------
result = json.loads(json.dumps(result).replace('(cid:299)', '').replace('\u2122', "'"))

# Output
os.makedirs(output_folder, exist_ok=True)
output_filename = os.path.splitext(os.path.basename(input_json_path))[0] + '.json'
with open(os.path.join(output_folder, output_filename), 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)

# Print
print(json.dumps(result, indent=4, ensure_ascii=False))
