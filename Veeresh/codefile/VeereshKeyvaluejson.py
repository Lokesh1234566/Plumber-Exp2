import json
import re

# Load table data
with open('../arrayjson/veeresh_1array.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load markdown text
with open('../mdfile/veeresh_1.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

result = {}

# Extract the first table
table_data = data[0]['tables'][0]
header_block = table_data[0][0]
lines = header_block.split('\n')

def extract_key_value_from_line(line):
    if ':' in line:
        key, value = line.split(':', 1)
        return key.strip(), value.strip()
    elif ' : ' in line:
        key, value = line.split(' : ', 1)
        return key.strip(), value.strip()
    return None, None

# Split between company and buyer
company_lines = []
buyer_lines = []
is_buyer = False
for line in lines:
    if line.strip().lower().startswith("customer"):
        is_buyer = True
        continue
    if is_buyer:
        buyer_lines.append(line.strip())
    else:
        company_lines.append(line.strip())

# Parse company info
for line in company_lines:
    key, value = extract_key_value_from_line(line)
    if key and value:
        result[key] = value
    elif line:
        result.setdefault("Company Info", []).append(line)

# Parse buyer info
for line in buyer_lines:
    key, value = extract_key_value_from_line(line)
    if key and value:
        result[f"Buyer {key}"] = value
    elif line:
        result.setdefault("Buyer Info", []).append(line)

# Convert multi-line fields
for k in ["Company Info", "Buyer Info"]:
    if k in result:
        result[k] = "\n".join(result[k])

# Metadata (e.g. Invoice No.)
for row in table_data:
    for cell in row:
        if cell and ':' in cell:
            for line in cell.split('\n'):
                key, value = extract_key_value_from_line(line)
                if key and value:
                    result[key] = value

# Items
item_rows = []
headers = []
start_idx = None
for idx, row in enumerate(table_data):
    if any("Description of Goods" in cell for cell in row):
        headers = [cell.replace('\n', ' ').strip() if cell else "" for cell in row]
        start_idx = idx + 1
        break

if headers and start_idx:
    for row in table_data[start_idx:]:
        if not any(row): continue
        if row[0] not in ['1', '2', '3']: continue
        item = {}
        for i, header in enumerate(headers):
            if header and i < len(row):
                val = row[i].strip()
                if header == "Amount" and '\n' in val:
                    parts = val.split('\n')
                    item["Amount"] = parts[0].strip()
                    if len(parts) > 1:
                        item["Tax"] = parts[1].strip()
                    if len(parts) > 2:
                        item["Round Off"] = parts[2].strip()
                else:
                    item[header] = val
        if "Sl No." in item:
            item["Sl"] = item.pop("Sl No.")
        item_rows.append(item)
        break  # only first item

if item_rows:
    result["Items"] = item_rows

# Fix malformed keys
if "(cid" in result:
    result["Total Amount"] = result.pop("(cid").replace(") ", "")

# ======================
# Extract from Markdown
# ======================

# Invoice No
invoice_match = re.search(r"Invoice No\.\s*\n\s*(\d+)", md_text)
if invoice_match:
    result["Invoice No"] = invoice_match.group(1)

# Dated
dated_match = re.search(r"Dated\s*\n\s*([\d\-A-Za-z]+)", md_text)
if dated_match:
    result["Dated"] = dated_match.group(1)

# Amount in words
amt_words_match = re.search(r"INR\s+(Ten Thousand[^\n]*)", md_text)
if amt_words_match:
    result["Amount Chargeable (in words)"] = f"INR {amt_words_match.group(1).strip()}"

# Tax Amount in words
tax_words_match = re.search(r"Tax Amount \(in words\)\s*:\s*(INR\s+[^\n]*)", md_text)
if tax_words_match:
    result["Tax Amount (in words)"] = tax_words_match.group(1).strip()

# Tax Breakdown
central_tax_match = re.search(r"Central Tax\s*Rate\s*Amount\s*\n\s*(\d+%)\s*\n\s*(\d+\.\d+)", md_text)
state_tax_match = re.search(r"State Tax\s*Rate\s*Amount\s*\n\s*(\d+%)\s*\n\s*(\d+\.\d+)", md_text)
total_tax_match = re.search(r"Total\s*Tax Amount\s*\n\s*(\d+\.\d+)", md_text)

if central_tax_match:
    result["Central Tax Rate"] = central_tax_match.group(1)
    result["Central Tax Amount"] = central_tax_match.group(2)

if state_tax_match:
    result["State Tax Rate"] = state_tax_match.group(1)
    result["State Tax Amount"] = state_tax_match.group(2)

if total_tax_match:
    result["Total Tax Amount"] = total_tax_match.group(1)

# Declaration
decl_match = re.search(r"We declare that this invoice shows.*?correct\.", md_text, re.DOTALL)
if decl_match:
    result["Declaration"] = decl_match.group(0).strip()

# Authorised Signatory
sign_match = re.search(r"for VEERESH AGENCY\s*Authorised Signatory", md_text)
if sign_match:
    result["Authorised Signatory"] = "for VEERESH AGENCY"

# Output
print(json.dumps(result, indent=4))

# Optional: Save to file
with open('cleaned_invoice_output.json', 'w', encoding='utf-8') as out_f:
    json.dump(result, out_f, indent=4)
