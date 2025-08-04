import json
import os
import ThreeDConstants
# ------------------------------
# Load JSON File
# ------------------------------
input_path = '../arrayjson/vaco_4.json'  # update path as needed
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

result = {}

# ------------------------------
# Extract Company Info
# ------------------------------
header_block = data[0]['tables'][0][0][0]
lines = header_block.split('\n')

company_lines = []
is_buyer = False

for line in lines:
    if line.strip().startswith(ThreeDConstants.Constant_Buyer_Info):
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
        result.setdefault(ThreeDConstants.Constant_Company_Info, []).append(line)

result[ThreeDConstants.Constant_Company_Info] = "\n".join(result[ThreeDConstants.Constant_Company_Info])

# ------------------------------
# Extract Buyer Info
# ------------------------------
buyer_block = data[0]['tables'][0][3][0]
buyer_lines = buyer_block.split('\n')
buyer_lines = [line.strip() for line in buyer_lines if line.strip()]
result[ThreeDConstants.Constant_Buyer_Info] = "\n".join(buyer_lines)

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

invoice_raw = safe_extract(0, 4)
if invoice_raw and ThreeDConstants.Constant_Invoice_No in invoice_raw:
    parts = invoice_raw.split("\n")
    if len(parts) >= 2:
        result[ThreeDConstants.Constant_Invoice_No] = parts[1].strip()

dated = safe_extract(0, 7)

if dated and ThreeDConstants.Constant_Invoice_Dated in dated:
    temp = dated.replace(ThreeDConstants.Constant_Vaco_Dated,"")
    # print(temp)
    # substring_to_find = "\n"
    # if substring_to_find in temp:
    #     result[ThreeDConstants.Constant_Invoice_Dated] = str(temp)  
    # else:
    #     result[ThreeDConstants.Constant_Invoice_Dated] = str(temp)
    result[ThreeDConstants.Constant_Vaco_Invoice_Dated] =str(temp)
    
    # print(dated.replace("Dated",""))
    # parts = dated.split("\n")
    # if len(parts) >= 2:
    #     result[ThreeDConstants.Constant_Dated] = parts[1].strip()
    # result[ThreeDConstants.Constant_Dated] = dated.split("\n")[-1].strip()

delivery_note = safe_extract(1, 4)
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

other_refs = safe_extract(2, 7)

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
# print(dated)
if dated:
  substring_to_find = "\n"
  if substring_to_find in dated:
        result[ThreeDConstants.Constant_Dated] = dated.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Dated] = ""



despatchdocumentno=safe_extract(4, 4)
# print(despatchdocumentno)
if despatchdocumentno:
  substring_to_find = "\n"
  if substring_to_find in despatchdocumentno:
        result[ThreeDConstants.Constant_Despatch_DocumentNo] = despatchdocumentno.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Despatch_DocumentNo] = ""

deliverynotedate=safe_extract(4, 7)
# print(deliverynotedate)
if deliverynotedate:
  substring_to_find = "\n"
  if substring_to_find in deliverynotedate:
        result[ThreeDConstants.Constant_Delivery_NoteDate ] = deliverynotedate.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Delivery_NoteDate] = ""
       
despatchedthrough=safe_extract(5, 4)
# print(despatchedthrough)
if despatchedthrough:
  substring_to_find = "\n"
  if substring_to_find in despatchedthrough:
        result[ThreeDConstants.Constant_Despatched_Through ] = despatchedthrough.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Despatched_Through] = ""

destination=safe_extract(5, 7)
# print(destination)
if destination:
  substring_to_find = "\n"
  if substring_to_find in destination:
        result[ThreeDConstants.Constant_Destination ] = destination.split("\n")[-1].strip()      
  else:
        result[ThreeDConstants.Constant_Destination] = ""    


termsofdelivery=safe_extract(6, 4)
# print(termsofdelivery)
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
    print(len(rows))
    print(row)
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
    elif row and any(ThreeDConstants.Constant_TotalAmount in str(cell) for cell in row):
        total_amount = row[-1].strip()
        i += 1
    elif row and any(ThreeDConstants.Constant_Total in str(cell) for cell in row):
        total = row[-1].strip()
        i += 1
        
    else:
        i += 1

if item_rows:
    result[ThreeDConstants.Constant_Items] = item_rows

if tax_rows:
    result[ThreeDConstants.Constant_Taxes] = tax_rows

if total_amount:
    result[ThreeDConstants.Constant_TotalAmount] = total_amount
    
i = 17

while i < len(rows):
    row = rows[i]
    
    if row  and any(ThreeDConstants.Constant_Total in str(cell) for cell in row):  
        total= row[-1].strip()
        print("TOTALLLLLLLLLLLL")
        i += 1
    else:
        i += 1
        
    result[ThreeDConstants.Constant_Total] = total

# ------------------------------
# Footer: Amount in Words & Bank
# ------------------------------
footer_row = table[-2][0] if table[-2] and table[-2][0] else ""
lines = footer_row.split("\n")

for line in lines:
    if ThreeDConstants.Constant_Amount_Chargeable in line or ThreeDConstants.Constant_IndianRupees in line:
        result[ThreeDConstants.Constant_Amount_ChargeableInWords] = line.replace(ThreeDConstants.Constant_Amount_EOE, "").strip()
    elif ThreeDConstants.Constant_BankName in line:
        result[ThreeDConstants.Constant_BankName] = line.split(":", 1)[1].strip()
    elif ThreeDConstants.COnstant_Account_no in line:
        result[ThreeDConstants.Constant_BankACNo] = line.split(":", 1)[1].strip()
    elif ThreeDConstants.Constant_IFS_Code in line:
        result[ThreeDConstants.Constant_Branch_IFS_Code] = line.split(":", 1)[1].strip()

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

# Print JSON
print(json.dumps(result, indent=4, ensure_ascii=False))

# Save to keyvaluejson folder
output_folder = 'keyvaluejsonVaco'
os.makedirs(output_folder, exist_ok=True)

output_filename = os.path.splitext(os.path.basename(input_path))[0] + '.json'
with open(os.path.join(output_folder, output_filename), 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)
