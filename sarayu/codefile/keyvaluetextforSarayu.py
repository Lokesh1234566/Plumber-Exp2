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
input_path = Path("../arrayjson/sarayu_74_06.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}
file_read = open("../mdfile/sarayu_74_06.md", "r")

    # asking the user to enter the string to be 
    # searched
text="Destination"
textNextLineDestinationShouldNotBe="Terms"
textNextLine=""
destinationValue=""
lines = file_read.readlines()
line_count = len(lines)
new_list = []
idx = 0
idx1=0
for line in lines:
        idx += 1
        idx1=idx +1
        # if line have the input string, get the index 
        # of that line and put the
        # line into newly created list 
        if text in line:
          
            print ("Line No %d - %s" % (idx, line))   
            if idx<line_count-1:   
             next_line = lines[idx + 1]
            print ("Next Line No %d - %s" % (idx+1, next_line))
            if  textNextLineDestinationShouldNotBe not in next_line:
             destinationValue=str(next_line)
             print ("destinationValue" + destinationValue.strip())
           
            break
   



text="Terms of Delivery"
termsofDeliveryValue=""
textNextLineTermsShouldNotBe="Description"
new_list = []
idx = 0
idx1=0
for line in lines:
        idx += 1
        idx1=idx +1
        # if line have the input string, get the index 
        # of that line and put the
        # line into newly created list 
        if text in line:
           
            print ("Line No %d - %s" % (idx, line))   
            if idx<line_count-1:   
             next_line = lines[idx + 1]
            print ("Next Line No %d - %s" % (idx+1, next_line))
            if  textNextLineTermsShouldNotBe not in next_line:
             termsofDeliveryValue=str(next_line)
             print ("termsofDeliveryValue" + termsofDeliveryValue.strip())
           
            break
    # closing file after reading
file_read.close()
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
buyer_block = data[0]['tables'][0][1][0]
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
        result[k] = "\n".join(result[k])

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
       
  

payment_terms = safe_extract(1, 11)
if payment_terms:
    result[ThreeDConstants.Constant_ModeTerms_Of_Payment] = payment_terms.split("\n")[-1].strip()

supplier_ref = safe_extract(0, 2)
if supplier_ref:
    parts = supplier_ref.split("\n")
    result[ThreeDConstants.Constant_Suppliers_Ref] = parts[4].strip() if len(parts) > 1 else supplier_ref

other_refs = safe_extract(0, 2)

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

deliverynotedate=safe_extract(5, 11)
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

destination=safe_extract(6, 11)
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





result["Destination"] = destinationValue.replace("\n", " ")
result["Terms of Delivery"] = termsofDeliveryValue.replace("\n", " ")

# ------------------------------
# Extract and Merge Item Rows
# ------------------------------
item_rows = []
header_row = None
start_idx = None
rows = table
table_rows = data[0]['tables'][0]
i = 8  # Start from items header


# Find header row
for idx, row in enumerate(table_rows):
    if row and any("Description of Goods" in str(cell) for cell in row):
        header_row = row
        start_idx = idx + 1
        break

if header_row and start_idx is not None:
    headers = [cell.replace("\n", " ").strip() if cell else "" for cell in header_row]
    data_row = table_rows[start_idx]
    split_columns = [cell.split("\n") if cell else [] for cell in data_row]
    max_len = max(len(col) for col in split_columns)

    for i in range(0, max_len - 1, 2):  # Step every 2 lines
        for j in range(2):  # Handle 2 entries per pair
            item = {}
            for col_idx, col_values in enumerate(split_columns):
                key = headers[col_idx]
                if not key:
                    continue

                val1 = col_values[i + j] if i + j < len(col_values) else ""
                val2 = col_values[i + j + 1] if (key == "Description of Goods" and i + j + 1 < len(col_values)) else ""

                if key == "Description of Goods":
                    item[key] = f"{val1.strip()} {val2.strip()}".strip()
                elif key == "Sl No.":
                    item["Sl"] = val1.strip()
                else:
                    item[key] = val1.strip()
            if item.get("Sl") and item.get("Description of Goods"):
                item_rows.append(item)

# Add to result
if item_rows:
    result["Items"] = item_rows

# ------------------------------
# Clean and Output Result
# ------------------------------

# ------------------------------
# Footer: Amount in Words & Bank
# ------------------------------
# ------------------------------
# Extract Footer Details as Structured Key-Value Pairs (Page 2)
# ------------------------------
footer_info = {}
bank_details = {}
buffer = []
current_section = None

page2_tables = data[0]["tables"][0]
strSplt=[]
for row in page2_tables:
    for cell in row:
        
        if cell and isinstance(cell, str):
            text = cell.strip()          
           
            if text.startswith("Amount Chargeable"):
               
                if "\n" in text:
                    key, val = text.split("\n")                              
                    footer_info["Amount Chargeable (in words)"] = val.strip()

            elif text.startswith("Tax Amount (in words)"):


              
                if ":" in text:
                    footerSplit =text.split("\n") 
                    for item in footerSplit:                      
                       itemSplit = item.split(":", 1)                     
                       if(itemSplit[0]).startswith("Company’s PAN") and (len(itemSplit))>1:
                        bank_details["Company’s PAN"] =itemSplit[1]                     
                       
                   
                    footer_info["Tax Amount (in words)"] = val.strip()

         
            elif text.startswith("Declaration for"):
                current_section = "Declaration"
                buffer = []

            elif "Authorised Signatory" in text:
                if current_section == "Declaration" and buffer:
                    footer_info["Declaration"] = " ".join(buffer).strip()
                    current_section = None
                footer_info["Authorised Signatory"] = text.replace("Authorised Signatory", "").strip()

            elif current_section == "Declaration":
                buffer.append(text)

if bank_details:
    footer_info["Bank Details"] = bank_details

if footer_info:
    result["Footer Info"] = footer_info


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

