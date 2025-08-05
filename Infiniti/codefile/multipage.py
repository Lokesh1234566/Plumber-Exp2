import json
from pathlib import Path

# Load Constants manually from file
constants_path = Path("../codefile/ThreeDConstants.py")
constants = {}
exec(constants_path.read_text(), constants)

# --- Set input file path ---
input_path = Path("../arrayjson/Infiniti1213.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}

# ----------------- Company Info (from first page only) -----------------
first_page = data[0]
tables = first_page['tables'][0]
header_block = tables[0][0]
lines = header_block.split('\n')

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

# ----------------- Buyer Info (from first page only) -----------------
buyer_block = None
for row in tables:
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

# ----------------- Invoice Info (from first page only) -----------------
invoice_block = tables[0][2]
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
        invoice_info["Delivery Note"] = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
    elif line.startswith("Mode/Terms of Payment"):
        invoice_info["Mode/Terms of Payment"] = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
    elif line.startswith("Supplier’s Ref."):
        invoice_info["Supplier’s Ref."] = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
    elif line.lower().startswith("destination"):
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        invoice_info["Destination"] = next_line
    elif line.lower().startswith("terms of delivery"):
        invoice_info["Terms Of Delivery"] = lines[idx + 1].strip() if idx + 1 < len(lines) else ""

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

# ----------------- Items (from all pages) -----------------
item_rows = []
for page in data:
    table = page['tables'][0]
    for idx, row in enumerate(table):
        if row and any("Description of Goods" in str(cell) for cell in row):
            for data_row in table[idx + 1:]:
                if not any(data_row):
                    break
                desc_lines = data_row[0].split("\n") if len(data_row) > 0 else []
                hsn = data_row[1].strip() if len(data_row) > 1 else ""
                qty = data_row[3].strip() if len(data_row) > 3 else ""
                rate = data_row[4].strip() if len(data_row) > 4 else ""
                amt = data_row[7].strip() if len(data_row) > 7 else ""

                service_description = []
                for line in desc_lines:
                    line = line.strip()
                    if "sgst" in line.lower():
                        item_rows.append({"type": "sgst", "rate": "9%", "amount": amt})
                    elif "cgst" in line.lower():
                        item_rows.append({"type": "cgst", "rate": "9%", "amount": amt})
                    else:
                        service_description.append(line)

                if service_description:
                    item_rows.append({
                        "type": "service",
                        "description": " ".join(service_description),
                        "hsn": hsn,
                        "rate": rate,
                        "amount": amt,
                        "quantity": qty
                    })

result["Items"] = item_rows

# ----------------- Tax Detail (from any page) -----------------
for page in data:
    table = page['tables'][0]
    for idx, row in enumerate(table):
        if row and any("Central Tax" in str(cell) for cell in row):
            tax_data_row = table[idx + 3]
            result["Tax Detail"] = {
                "HSN/SAC": tax_data_row[0].strip(),
                "taxable_value": tax_data_row[2].strip(),
                "central_tax_rate": tax_data_row[5].strip(),
                "central_tax_amount": tax_data_row[7].strip(),
                "state_tax_rate": tax_data_row[10].strip(),
                "state_tax_amount": tax_data_row[13].strip(),
                "total_tax": tax_data_row[17].strip()
            }
            break

# ----------------- Footer Info & Bank Details (from any page) -----------------
footer_info = {}
bank_details = {}

for page in data:
    for row in page["tables"][0]:
        for cell in row:
            if not isinstance(cell, str):
                continue
            text = cell.strip()
            if text.startswith("Amount Chargeable") and "\n" in text:
                _, val = text.split("\n", 1)
                footer_info["Amount Chargeable (in words)"] = val.strip()
            elif text.startswith("Tax Amount (in words)"):
                lines = text.split("\n")
                footer_info["Tax Amount (in words)"] = lines[0].split(":", 1)[-1].strip()
                for line in lines[1:]:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        bank_details[key.strip()] = value.strip()
                break
        if footer_info:
            break
    if footer_info:
        break

if bank_details:
    footer_info["Bank Details"] = bank_details
if footer_info:
    result["Footer Info"] = footer_info

# ----------------- Save Output JSON -----------------
output_dir = Path("../keyvaluemainjson")
output_dir.mkdir(parents=True, exist_ok=True)

output_file_path = output_dir / input_path.name
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"✅ Output saved to: {output_file_path}")
