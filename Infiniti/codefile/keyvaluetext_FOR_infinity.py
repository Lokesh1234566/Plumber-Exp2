import json
from pathlib import Path
import re

# Load Constants manually from file
constants_path = Path("../codefile/ThreeDConstants.py")
constants = {}
exec(constants_path.read_text(), constants)

# Load JSON data
# --- Set input file path ---
input_path = Path("../arrayjson/Infiniti1213.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}
# print(len(data))

# ----------------- Company Info -----------------
header_block = data[0]['tables'][0][0][0]
lines = header_block.split('\n')
pagecount = len(data)

company_info_structured = {}
address_lines = []
for line in lines:
    line = line.strip()
    if line.lower().startswith("buyer"):
        break
    if "PH:" in line:
        company_info_structured["Phone"] = line.split("PH:")[-1].strip()
    elif "PAN NO" in line:
        company_info_structured["PAN"] = line.split("PAN NO:")[-1].strip()
    elif "GSTIN/UIN" in line:
        company_info_structured["GSTIN/UIN"] = line.split("GSTIN/UIN:")[-1].strip()
    elif "E-Mail" in line:
        company_info_structured["Email"] = line.split("E-Mail :")[-1].strip()
    elif "State Name" in line:
        parts = line.split("Code :")
        if len(parts) == 2:
            company_info_structured["State"] = parts[0].split(":")[-1].strip().strip(",")
            company_info_structured["State Code"] = parts[1].strip()
    else:
        address_lines.append(line)

if address_lines:
    company_info_structured["Name"] = address_lines[0]
    company_info_structured["Address"] = "\n".join(address_lines[1:])

result[constants["Constant_Company_Info"]] = company_info_structured
# ----------------- Buyer Info -----------------

table = data[pagecount-1]['tables'][0]

def safe_extract(row_idx, col_idx):
    try:
        cell = table[row_idx][col_idx]
        return cell.strip() if cell else ""
    except IndexError:
        return ""  

invoice_raw = safe_extract(8, 0)
print(invoice_raw)
if invoice_raw and "RENTAL" in invoice_raw:
    parts = invoice_raw.split("RENTAL")
    if len(parts) >= 2:
        #result[ThreeDConstants.Constant_Invoice_No] = parts[0].split(":")[1]
        result["Date of Invoice"] = parts[1].split(":")[1]
# ----------------- Buyer Info -----------------
buyer_block = None
for row in data[0]['tables'][0]:
    for cell in row:
        if cell and "Buyer\n" in cell:
            buyer_block = cell
            break
    if buyer_block:
        break

buyer_info_structured = {}
if buyer_block:
    lines = buyer_block.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    if lines[0].lower().startswith("buyer"):
        lines = lines[1:]
    if lines:
        buyer_info_structured["Name"] = lines[0]
    address_lines = []
    for line in lines[1:]:
        if "GSTIN" in line or "State Name" in line:
            continue
        address_lines.append(line)
    if address_lines:
        buyer_info_structured["Address"] = "\n".join(address_lines)

    for line in lines:
        if "GSTIN" in line.upper():
            parts = line.split(":", 1)
            if len(parts) == 2:
                buyer_info_structured["GSTIN/UIN"] = parts[1].strip()
        elif "State Name" in line:
            state_match = line.split("Code")
            if len(state_match) == 2:
                state = state_match[0].split(":")[-1].strip().strip(",")
                code = state_match[1].split(":")[-1].strip()
                buyer_info_structured["State"] = state
                buyer_info_structured["State Code"] = code

result[constants["Constant_Buyer_Info"]] = buyer_info_structured

# ----------------- Invoice Info (Dynamic) -----------------
invoice_block = data[pagecount-1]['tables'][0][0][3]
lines = invoice_block.split('\n')

invoice_info = {
    "Invoice No": "",
    "Dated": "",
    "Delivery Note": "",
    "Mode/Terms of Payment": "",
    "Supplier’s Ref.": "",
    "Other Reference(s)": "",
    "Buyer's Order No.": "",
    "Despatch Document No.": "",
    "Delivery Note Date": "",
    "Despatched through": "",
    "Destination": "",
    "Terms Of Delivery": ""
}

for idx, line in enumerate(lines):
    line = line.strip()

    if line.startswith("Invoice No"):
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        parts = next_line.split()
        if len(parts) >= 2:
            invoice_info["Invoice No"] = parts[0]
            invoice_info["Dated"] = " ".join(parts[1:])
    elif line.startswith("Delivery Note"):
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        if next_line.lower() in ["mode/terms of payment", "mode / terms of payment"]:
            next_line = ""
        invoice_info["Mode/Terms of Payment"] = ""
    elif line.startswith("Supplier’s Ref."):
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        invoice_info["Supplier’s Ref."] = next_line
    elif "destination" in line.lower():
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        if next_line.lower().startswith("terms of delivery"):
            invoice_info["Destination"] = ""
        else:
            invoice_info["Destination"] = next_line


# Assign dynamically parsed invoice info
result[constants["Constant_Invoice_No"]] = invoice_info["Invoice No"]
result[constants["Constant_Dated"]] = invoice_info["Dated"]
result[constants["Constant_Delivery_Note"]] = invoice_info["Delivery Note"]
result[constants["Constant_ModeTerms_Of_Payment"]] = invoice_info["Mode/Terms of Payment"]
result[constants["Constant_Suppliers_Ref"]] = invoice_info["Supplier’s Ref."]
result[constants["Constant_Other_Reference"]] = invoice_info["Other Reference(s)"]
result[constants["Constant_Buyer_OrderNo"]] = invoice_info["Buyer's Order No."]
result[constants["Constant_Despatch_DocumentNo"]] = invoice_info["Despatch Document No."]
result[constants["Constant_Delivery_NoteDate"]] = invoice_info["Delivery Note Date"]
result[constants["Constant_Despatched_Through"]] = invoice_info["Despatched through"]
result[constants["Constant_Destination"]] = invoice_info["Destination"]
result[constants["Constant_TermsOfDelivery"]] = invoice_info["Terms Of Delivery"]

# ----------------- Items -----------------
item_rows = []
for page_number in range(0, pagecount):
    # print(page_number)
    for idx, row in enumerate(data[page_number]['tables'][0]):
        if row and any("Description of Goods" in str(cell) for cell in row):
            headers = [cell.strip().replace("\n", " ") if cell else "" for cell in row]
            data_row = data[page_number]['tables'][0][idx + 1]
            # print(data_row)
            break

desc_lines = data_row[0].split("\n") if len(data_row) > 0 else []
print(desc_lines)
hsn = data_row[2].strip() if len(data_row) > 2 else ""
rate_lines = data_row[7].split("\n") if len(data_row) > 7 else []
# raw_amount = data_row[16] if len(data_row) > 16 else ""
# amount_lines =data_row[16] if len(data_row) > 16 else ""
# Get the current and next row after 'Description of Goods'
data_row = data[page_number]['tables'][0][idx + 1]
next_row = data[page_number]['tables'][0][idx + 2] if len(data[page_number]['tables'][0]) > idx + 2 else []

# Extract amounts from the NEXT row's 16th column
raw_amount = next_row[16] if len(next_row) > 16 else ""
amount_lines = [amt.replace(",", "").strip() for amt in raw_amount.split("\n") if amt.strip()]
# print("Amount lines:", amount_lines)

service_description = []
for i, line in enumerate(desc_lines):
    line = line.strip()
    if "sgst" in line.lower():
        # Extract percentage using regex
        match = re.search(r'(\d+%)', line)
        rate = match.group(1) if match else (rate_lines[1] if len(rate_lines) > 1 else "")
        amount = amount_lines[1] if len(amount_lines) > 1 else ""
        item_rows.append({"type": "sgst", "rate": rate, "amount": amount})
    elif "cgst" in line.lower():
        match = re.search(r'(\d+%)', line)
        rate = match.group(1) if match else (rate_lines[2] if len(rate_lines) > 2 else "")
        amount = amount_lines[2] if len(amount_lines) > 2 else ""
        item_rows.append({"type": "cgst", "rate": rate, "amount": amount})
    else:
        service_description.append(line)

if service_description:
    item_rows.insert(0, {
        "type": "service",
        "description": " ".join(service_description),
        "hsn": hsn,
        "rate": rate_lines[0] if rate_lines else "",
        "amount": amount_lines[0] if amount_lines else "",
        "quantity": ""
    })

# ----------------- Tax Detail -----------------
for page_number in range(0, pagecount):
    print(page_number)
for idx, row in enumerate(data[page_number]['tables'][0]):
    if row and any("Central Tax" in str(cell) for cell in row):      
        tax_data_row = data[page_number]['tables'][0][idx + 2]
        item_rows.append({
            "type": "tax_detail",
            "HSN/SAC": tax_data_row[0].strip(),
            "taxable_value": tax_data_row[2].strip(),
            "central_tax_rate": tax_data_row[5].strip(),
            "central_tax_amount": tax_data_row[7].strip(),
            "state_tax_rate": tax_data_row[10].strip(),
            "state_tax_amount": tax_data_row[13].strip(),
            "total_tax": tax_data_row[17].strip()
        })
        break

result["Items"] = item_rows

# ----------------- Footer -----------------
footer_info = {}
bank_details = {}
for row in data[0]["tables"][0]:
    for cell in row:
        if cell and isinstance(cell, str):
            text = cell.strip()
            if text.startswith("Amount Chargeable") and "\n" in text:
                _, val = text.split("\n", 1)
                footer_info["Amount Chargeable (in words)"] = val.strip()
            elif text.startswith("Tax Amount (in words)"):
        # Extract the actual tax amount line FIRST
                first_line = text.split("\n", 1)[0]
                temp = text.split("Company’s Bank Details")
                # print(temp[0])
                if ":" in first_line:
                    tax_label, tax_value = first_line.split(":", 1)
                    footer_info["Tax Amount (in words)"] = tax_value.strip()
                else:
                    footer_info["Tax Amount (in words)"] = ""

                footerSplit = text.split("\n")
                for item in footerSplit[1:]:
                    itemSplit = item.split(":", 1)
                    if len(itemSplit) != 2:
                        continue
                    key, value = itemSplit[0].strip(), itemSplit[1].strip()
                    if key.startswith("Bank Name"):
                        bank_details["Bank Name"] = value
                    elif key.startswith("A/c No."):
                        bank_details["A/c No."] = value
                    elif key.startswith("Branch & IFS Code"):
                        bank_details["Branch & IFS Code"] = value
                    elif key.startswith("Company’s Service Tax No."):
                        parts = value.split("A/c No. :")
                        if len(parts) == 2:
                            bank_details["Company’s Service Tax No."] = parts[0].strip()
                            bank_details["A/c No."] = parts[1].strip()
                    elif key.startswith("Company’s PAN"):
                        parts = value.split("Branch")
                        bank_details["Company’s PAN"] = parts[0].strip()
                        if len(parts) > 1:
                            bank_details["Branch & IFS Code"] = parts[1].replace("& IFS Code :", "").strip()
                    elif key.startswith("Declaration for"):
                        bank_details["Declaration"] = key  # Note: declaration text may be multiline

                    footer_info["Tax Amount (in words)"] = temp[0].replace("Tax Amount (in words) :", "").strip()
            elif "Authorised Signatory" in text:
                footer_info["Authorised Signatory"] = text.replace("Authorised Signatory", "").strip()

if bank_details:
    footer_info["Bank Details"] = bank_details
if footer_info:
    result["Footer Info"] = footer_info

# Output JSON
output_dir = Path("../keyvaluemainjson")
output_dir.mkdir(parents=True, exist_ok=True)

output_file_path = output_dir / 'abcdef.json' # Uses the same filename

with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Output saved to: {output_file_path}")
