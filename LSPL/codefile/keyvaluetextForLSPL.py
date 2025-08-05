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
input_path = Path("../arrayjson/LSPL_356_01.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}
file_read = open("../mdfile/LSPL_356_01.md", "r")

lines = file_read.readlines()
line_count = len(lines)
next_line=''
idx = 0
idx1=0

# ------------------------------
# Extract Company and Buyer Info
# ------------------------------
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

company_lines = []
buyer_lines = []
is_buyer = False

for line in lines:
    
    if line.strip() == "Buyer":     
        is_buyer = True    
        continue
    if is_buyer:
        buyer_lines.append(line.strip())
    else:
        company_lines.append(line.strip())

for line in company_lines:
    key, value = extract_key_value_from_line(line)
    if key and value:
        result[key] = value
    elif line:
        result.setdefault("Company Info", []).append(line)

for line in buyer_lines:   
    key, value = extract_key_value_from_line(line)
    
    if key and value:
        result[f"Buyer {key}"] = value
    elif line:        
        result.setdefault("Buyer Info", []).append(line)

for k in ["Company Info", "Buyer Info"]:
    if k in result:
        result[k] = "\n".join(result[k])

# ------------------------------
# Extract Buyer Info
# ------------------------------
"""buyer_block = data[0]['tables'][0][1][0]
buyer_lines = buyer_block.split('\n')
print(buyer_lines)

buyer_lines = [line.strip() for line in buyer_lines if line.strip()]
for line in buyer_lines:   
    key, value = extract_key_value_from_line(line)
    
    if key and value:
        result[key] = value
    elif line:        
        result.setdefault("Buyer Info", []).append(line)

for k in ["Buyer Info"]:
    if k in result:
        result[k] = "\n".join(result[k])"""

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



test = safe_extract(3, 0).split("\n")
print(test)
if test :
    for line in test:   
     
     key, value = extract_key_value_from_line(line)
    
    if key and value:
        result[f"Buyer {key}"] = value
    elif line:        
        result.setdefault("Buyer Info", []).append(line)
  

invoice_raw = safe_extract(0, 2)
if invoice_raw and ThreeDConstants.Constant_Invoice_No in invoice_raw:
    parts = invoice_raw.split("\n")
    if len(parts) >= 2:
        result[ThreeDConstants.Constant_Invoice_No] = parts[1].split(" ")[0]

dated = safe_extract(0, 2)
if dated and ThreeDConstants.Constant_Dated in dated:
    result[ThreeDConstants.Constant_Dated] = dated.split("\n")[-1].strip()

delivery_note = safe_extract(0, 2)
if delivery_note:
    substring_to_find = "\n"
    if substring_to_find in delivery_note:
        result[ThreeDConstants.Constant_Delivery_Note] = delivery_note  
    else:
        result[ThreeDConstants.Constant_Delivery_Note] = ""
       
  

payment_terms = safe_extract(1, 7)
if payment_terms:
    result[ThreeDConstants.Constant_ModeTerms_Of_Payment] = payment_terms.split("\n")[-1].strip()

supplier_ref = safe_extract(2, 4)
if supplier_ref:
    parts = supplier_ref.split("\n")
    result[ThreeDConstants.Constant_Suppliers_Ref] = parts[1].strip() if len(parts) > 1 else supplier_ref

other_refs = safe_extract(2, 10)

if other_refs:
    substring_to_find = "\n"
    if substring_to_find in other_refs:
        result[ThreeDConstants.Constant_Other_Reference] = other_refs.split("\n")[-1].strip()      
    else:
        result[ThreeDConstants.Constant_Other_Reference] = ""
       
buyer_order_no=safe_extract(3, 4)

if buyer_order_no:
  substring_to_find = "\n"
  if substring_to_find in buyer_order_no:
        result[ThreeDConstants.Constant_Buyer_OrderNo] = buyer_order_no.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Buyer_OrderNo] = ""


dated=safe_extract(3, 7)
print(dated)
if dated:
  substring_to_find = "\n"
  if substring_to_find in dated:
        result[ThreeDConstants.Constant_Dated] = dated.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Dated] = ""



despatchdocumentno=safe_extract(4, 4)
print(despatchdocumentno)
if despatchdocumentno:
  substring_to_find = "\n"
  if substring_to_find in despatchdocumentno:
        result[ThreeDConstants.Constant_Despatch_DocumentNo] = despatchdocumentno.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Despatch_DocumentNo] = ""

deliverynotedate=safe_extract(4, 7)
print(deliverynotedate)
if deliverynotedate:
  substring_to_find = "\n"
  if substring_to_find in deliverynotedate:
        result[ThreeDConstants.Constant_Delivery_NoteDate ] = deliverynotedate.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Delivery_NoteDate] = ""
       
despatchedthrough=safe_extract(5, 4)
print(despatchedthrough)
if despatchedthrough:
  substring_to_find = "\n"
  if substring_to_find in despatchedthrough:
        result[ThreeDConstants.Constant_Despatched_Through ] = despatchedthrough.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Despatched_Through] = ""

destination=safe_extract(5, 7)
print(destination)
if destination:
  substring_to_find = "\n"
  if substring_to_find in destination:
        result[ThreeDConstants.Constant_Destination ] = destination.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Destination] = ""    


termsofdelivery=safe_extract(6, 4)
print(termsofdelivery)
if termsofdelivery:
  substring_to_find = "\n"
  if substring_to_find in termsofdelivery:
        result[ThreeDConstants.Constant_TermsOfDelivery ] = termsofdelivery.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_TermsOfDelivery] = ""     








# ------------------------------
# Extract Items, Taxes, Totals
# ------------------------------
item_rows = []
tax_rows = []
total_amount = ""
total = ""

rows = table
i = 8  # Start from items header

while i < len(rows):
    row = rows[i]

    if row and row[0] and row[0].strip().isdigit():
        sl_no = row[0].strip()
        description_parts = []

        # First description line (might be empty)
        if len(row) > 2 and row[2]:
            description_parts.append(row[2].strip())

        hsn = row[5].strip() if len(row) > 5 and row[5] else ""
        rate = row[6].strip() if len(row) > 6 and row[6] else ""
        amount = row[9].strip() if len(row) > 9 and row[9] else ""

        # Look ahead for continuation lines (no SL No, description in col 2)
        j = i + 1
        while j < len(rows) and (not rows[j][0] or not rows[j][0].strip().isdigit()):
            cont_row = rows[j]
            if len(cont_row) > 2 and cont_row[2]:
                description_parts.append(cont_row[2].strip())
            j += 1

        description = " ".join(description_parts)

        if description.lower() in [ThreeDConstants.Constant_CGST, ThreeDConstants.Constant_SGST]:
            tax_rows.append({
                ThreeDConstants.Constant_Type: description,
                ThreeDConstants.Constant_Rate: rate,
                ThreeDConstants.Constant_Amount: amount
            })
        else:
            item_rows.append({
                ThreeDConstants.Constant_Sl: sl_no,
                ThreeDConstants.Constant_DescriptionVaco: description,
                ThreeDConstants.Constant_HSN_SAC: hsn,
                ThreeDConstants.Constant_Rate: rate,
                ThreeDConstants.Constant_Amount: amount
            })

        i = j  # Skip processed lines
    elif row and any(ThreeDConstants.Constant_Total in str(cell) for cell in row):
        total_amount = row[-1].strip()
        i += 1
    else:
        i += 1

    


if item_rows:
    result[ThreeDConstants.Constant_Items] = item_rows

if tax_rows:
    result[ThreeDConstants.Constant_Taxes] = tax_rows

if total_amount:
    result[ThreeDConstants.Constant_TotalAmount] = total_amount

i = 0

while i < len(rows):
    row = rows[i]    
    if row  and any(ThreeDConstants.Constant_Total in str(cell) for cell in row):  
        total= row[-1].strip()
        #print("TOTALLLLLLLLLLLL")
        i += 1
    else:
        i += 1

 
if total:
    result[ThreeDConstants.Constant_Total] = total





# ------------------------------
# Clean and Output Result
# ------------------------------

# ------------------------------
# Footer: Amount in Words & Bank
# ------------------------------

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
                if ":" in text:
                    footerSplit = text.split("\n")
                    for item in footerSplit:
                        itemSplit = item.split(":", 1)
                        print(item) 
                        #print(itemSplit[0]) 
                       
                        if itemSplit[0].startswith("Bank Name"):
                            bank_details["Bank Name"] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("A/c"):
                            bank_details["A/c No."] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("Branch & IFS Code"):
                            bank_details["Branch & IFS Code"] = itemSplit[1].strip()
                        elif itemSplit[0].startswith("Company's Service"):
                            print(itemSplit[0])
                            print(itemSplit[1].split("A/c") [0])
                            parts = itemSplit[0].split("A/c")  
                            bank_details["Company’s Service Tax No."] = itemSplit[1].split("A/c") [0]                         
                               
                            bank_details["A/c No."] = itemSplit[1].split("A/c") [1].replace("No. :", "").strip()  
                        elif itemSplit[0].startswith("Company's PAN"):
                            parts = itemSplit[0].split("Branch")
                            bank_details["Company’s PAN"] =  itemSplit[1].split("Branch") [0]  
                            bank_details["Branch & IFS Code"] = itemSplit[1].split("Branch & IFS Code:") [1].replace("Branch & IFS Code:", "").strip()        
                           
                        elif itemSplit[0].startswith("Declaration for"):
                            bank_details["Declaration"] = itemSplit[0].strip()
                  
            elif "Authorised Signatory" in text:
                footer_info["Authorised Signatory"] = text.replace("Authorised Signatory", "").strip()

if bank_details:
    footer_info["Bank Details"] = bank_details
if footer_info:
    result["Footer Info"] = footer_info
# ------------------------------
# Extract Footer Details as Structured Key-Value Pairs (Page 2)
# ------------------------------

# ------------------------------
# Authorised Signatory
# ------------------------------
sign_line = table[-1][3]
if sign_line and isinstance(sign_line, str):
    lines = sign_line.split("\n")
    result[ThreeDConstants.Constant_Authorised_Signatory] = lines[-1].strip()

# ------------------------------
# Clean and Save JSON
# ------------------------------
result = json.loads(json.dumps(result).replace(ThreeDConstants.Constant_cid299, '').replace(ThreeDConstants.Constant_u2122, "'"))

# Output JSON
output_dir = Path("../keyvaluemainjson")
output_dir.mkdir(parents=True, exist_ok=True)

output_file_path = output_dir / input_path.name # Uses the same filename

with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Output saved to: {output_file_path}")

