import json
from pathlib import Path
import re
import ThreeDConstants
# Load Constants manually from file
constants_path = Path("../codefile/ThreeDConstants.py")
constants = {}
exec(constants_path.read_text(), constants)

# Load JSON data
# --- Set input file path ---
input_path = Path("../arrayjson/brindavan.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}

# ----------------- Company Info -----------------
header_block = data[0]['tables'][0][0][0]
lines = header_block.split('\n')

def extract_key_value_from_line(line):
    if ':' in line:
        key, value = line.split(':', 1)
        return key.strip(), value.strip()
    elif ' : ' in line:
        key, value = line.split(' : ', 1)
        return key.strip(), value.strip()
    return None, None

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
    elif "GSTIN" in line:
        company_info_structured["GSTIN"] = line.split("GSTIN:")[-1].strip()
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
        if "GSTIN" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                buyer_info_structured["GSTIN/UIN"] = parts[1].strip()
        if "State Name" in line:
            parts = line.split(":")
            if len(parts) == 2 and "Code" in parts[1]:
                state_part, code_part = parts[1].split("Code")
                buyer_info_structured["State"] = state_part.strip().strip(",")
                buyer_info_structured["State Code"] = code_part.strip(" :")

result[constants["Constant_Buyer_Info"]] = buyer_info_structured

# ----------------- Invoice Info -----------------
# ------------------------------
# Extract Invoice Meta Info
# ------------------------------
table = data[0]['tables'][0]

def safe_extract(row_idx, col_idx):
    try:
        cell = table[row_idx][col_idx]
        return cell.strip() if cell else ""
    except IndexError:
        return ""  

invoice_raw = safe_extract(1, 0)
print(invoice_raw)
if invoice_raw and "Invoice No." in invoice_raw:
    parts = invoice_raw.split("\n")
    if len(parts) >= 2:
        result[ThreeDConstants.Constant_Invoice_No] = parts[0].split(":")[1]
        result["Date of Invoice"] = parts[1].split(":")[1]

party_po_number= safe_extract(1, 4)
print(party_po_number)
if party_po_number and "Party" in party_po_number:
    parts = party_po_number.split("\n")
    if len(parts) >= 2:
        result["Party's P.O No."] = parts[0].split(":")[1]
        result["State Code"] = parts[1].split(":")[1]


billed_to= safe_extract(2, 0)
print(billed_to)
if billed_to and "Billed" in billed_to:
    parts = billed_to.split("Customer")
    if len(parts) >= 2:        
        result["Billed To"] =  parts[0].split(":")[1].replace("\n","")
        result["Customer GSTIN"] =  parts[1].split(":")[1].replace("\n","")

shipped_to= safe_extract(2, 4)
print(shipped_to)
if shipped_to and "Shipped" in shipped_to:
    parts = shipped_to.split("Customer")
    if len(parts) >= 2:        
        result["Shipped To"] =  parts[0].replace("Shipped to :","").replace("\n","")
        result["Customer Mobile Number"] =  parts[1].split(":")[1].replace("\n","")



# ----------------- Items -----------------
item_rows = []
for idx, row in enumerate(data[0]['tables'][0]):
   
    if row and any("S.N" in str(cell) for cell in row):
        headers = [cell.strip().replace("\n", " ") if cell else "" for cell in row]
        data_row = data[0]['tables'][0][idx + 1]
        print(data_row)
        break

desc_lines = data_row[0].split("\n") if len(data_row) > 0 else []
hsn = data_row[2].strip() if len(data_row) > 2 else ""
rate_lines = data_row[7].split("\n") if len(data_row) > 7 else []
amount_lines = data_row[13].split("\n") if len(data_row) > 13 else []

service_description = []
for i, line in enumerate(desc_lines):
    line = line.strip()
    if line.lower().startswith("sgst"):
        item_rows.append({"type": "sgst", "rate": rate_lines[i] if i < len(rate_lines) else "", "amount": amount_lines[i] if i < len(amount_lines) else ""})
    elif line.lower().startswith("cgst"):
        item_rows.append({"type": "cgst", "rate": rate_lines[i] if i < len(rate_lines) else "", "amount": amount_lines[i] if i < len(amount_lines) else ""})
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
for idx, row in enumerate(data[0]['tables'][0]):
  
    if row and any("Central Tax" in str(cell)  for cell in row):      
        tax_data_row = data[0]['tables'][0][idx + 2]      
        print(tax_data_row)
        item_rows.append({
            "type": "tax_detail",
            "hsn": tax_data_row[0].strip(),
            "taxable_value": tax_data_row[1].strip(),
            "central_tax_rate": tax_data_row[4].strip(),
            "central_tax_amount": tax_data_row[6].strip(),
            "state_tax_rate": tax_data_row[8].strip(),
            "state_tax_amount": tax_data_row[10].strip(),
            "total_tax": tax_data_row[13].strip()
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
                if ":" in text:
                    footerSplit = text.split("\n")
                    for item in footerSplit:
                        itemSplit = item.split(":", 1)
                        if itemSplit[0].startswith("Bank Name"):
                            bank_details["Bank Name"] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("A/c No."):
                            bank_details["A/c No."] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("Branch & IFS Code"):
                            bank_details["Branch & IFS Code"] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("Company’s Service Tax No."):
                            parts = itemSplit[1].split("A/c No. :")
                            if len(parts) == 2:
                                bank_details["Company’s Service Tax No."] = parts[0].strip()
                                bank_details["A/c No."] = parts[1].strip()
                        elif itemSplit[0].startswith("Company’s PAN"):
                            parts = itemSplit[1].split("Branch")
                            bank_details["Company’s PAN"] = parts[0].strip()
                            if len(parts) > 1:
                                bank_details["Branch & IFS Code"] = parts[1].replace("& IFS Code :", "").strip()
                        elif itemSplit[0].startswith("Declaration for"):
                            bank_details["Declaration"] = itemSplit[0].strip()
                    footer_info["Tax Amount (in words)"] = itemSplit[-1].strip()
            elif "Authorised Signatory" in text:
                footer_info["Authorised Signatory"] = text.replace("Authorised Signatory", "").strip()

if bank_details:
    footer_info["Bank Details"] = bank_details
if footer_info:
    result["Footer Info"] = footer_info

# Output JSON
output_dir = Path("../keyvaluemainjson")
output_dir.mkdir(parents=True, exist_ok=True)

output_file_path = output_dir / input_path.name # Uses the same filename

with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Output saved to: {output_file_path}")

