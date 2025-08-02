import json
import os
import ThreeDConstants
# ------------------------------
# Load JSON File
# ------------------------------
input_path = '../pdf/sb_tech_1_array.json'  # Update path if needed
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

result = {}

# ------------------------------
# Extract Company Info
# ------------------------------
header_block = data[0][ThreeDConstants.Constant_Tables][0][0][0]
lines = header_block.split('\n')

company_lines = []
is_buyer = False

for line in lines:
    if line.strip().startswith(ThreeDConstants.Constant_Buyer):
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
        result.setdefault(ThreeDConstants.Constant_Company_SB, []).append(line)

result[ThreeDConstants.Constant_Company_SB] = "\n".join(result[ThreeDConstants.Constant_Company_SB])

# ------------------------------
# Extract Buyer Info (Not present, so skipped)
# ------------------------------
# result["Buyer Info"] = ""  # Placeholder if needed

# ------------------------------
# Extract Invoice Meta Info
# ------------------------------
table = data[0][ThreeDConstants.Constant_Tables][0]

def safe_extract(row_idx, col_idx):
    try:
        cell = table[row_idx][col_idx]
        return cell.strip() if cell else ""
    except IndexError:
        return ""

invoice_no = safe_extract(0, 4)
if invoice_no:
    result[ThreeDConstants.Constant_Invoice] = invoice_no

dated = safe_extract(0, 6)
if dated:
    result[ThreeDConstants.Constant_SBTech_Date] = dated
    
# other_refs = safe_extract(2, 7)

# if other_refs:
#     substring_to_find = "\n"
#     if substring_to_find in other_refs:
#         result[ThreeDConstants.Constant_Other_Reference] = other_refs.split("\n")[-1].strip()      
#     else:
#         result[ThreeDConstants.Constant_Other_Reference] = ""

our_dc_no = safe_extract(2, 3)
if our_dc_no:
    substring_to_find = "\n"
    if substring_to_find in our_dc_no:
        result[ThreeDConstants.Constant_SBTech_OurDCNo] = our_dc_no.split("\n")[-1].strip()
    else:
        result[ThreeDConstants.Constant_SBTech_OurDCNo]=""
        
our_dc_date = safe_extract(2, 5)

if our_dc_date:
    substring_to_find = "\n"
    if substring_to_find in our_dc_date:
        result[ThreeDConstants.Constant_SBTech_OurDCDate] = our_dc_date.split("\n")[-1].strip()
    else:
        result[ThreeDConstants.Constant_SBTech_OurDCDate]=""

your_dc_no = safe_extract(3,3)        
if your_dc_no:
    substring_to_find = "\n"
    if substring_to_find in your_dc_no:
        result[ThreeDConstants.Constant_SBTech_YourDCNo] = your_dc_no.split("\n")[-1].strip()
    else:
        result[ThreeDConstants.Constant_SBTech_YourDCNo]=""  
        
your_dc_date = safe_extract(3,5)        
if your_dc_date:
    substring_to_find = "\n"
    if substring_to_find in your_dc_date:
        result[ThreeDConstants.Constant_SBTech_YourDCDate] = your_dc_date.split("\n")[-1].strip()
    else:
        result[ThreeDConstants.Constant_SBTech_YourDCDate]=""
        
your_po_no = safe_extract(4,4)        
if your_po_no:
    result[ThreeDConstants.Constant_SBTech_YourPONo] = your_po_no
    # substring_to_find = "\n"
    # if substring_to_find in your_po_no:
    #     result["Your P.O. No"] = your_po_no.split("\n")[-1].strip()
    # else:
    #     result["Your P.O. No"]=""
        
your_po_date = safe_extract(4,6)        
if your_po_date:
    result[ThreeDConstants.Constant_SBTech_YourPODate] = your_po_date
    # substring_to_find = "\n"
    # if substring_to_find in your_po_date:
    #     result["Your P.O date"] = your_po_date.split("\n")[-1].strip()
    # else:
    #     result["Your P.O date"]=""
    
consignee_GST = safe_extract(5,0)        
if consignee_GST:
    result[ThreeDConstants.Constant_SBTech_Consignee] = consignee_GST
    
payment_Terms = safe_extract(5,3)        
if payment_Terms:
    result[ThreeDConstants.Constant_SBTech_Payment_Terms] = payment_Terms

payment_terms = safe_extract(5, 0)
if payment_terms and ThreeDConstants.Constant_SBTech_Payment_Terms in payment_terms:
    parts = payment_terms.split(ThreeDConstants.Constant_SBTech_Payment_Terms, 1)[1].split("\n")
    result[ThreeDConstants.Constant_SBTech_Mode_Terms_Payment] = parts[0].strip()

supplier_ref = safe_extract(2, 4)
if supplier_ref:
    result[ThreeDConstants.Constant_SBTech_Supplier_Ref] = supplier_ref

other_refs = safe_extract(3, 4)
if other_refs:
    result[ThreeDConstants.Constant_SBTech_Other_Ref] = other_refs

# ------------------------------
# Extract Items, Taxes, Totals
# ------------------------------
item_rows = []
tax_rows = []
total_amount = ""

rows = table
i = 6  # Start from items header

while i < len(rows):
    row = rows[i]
    if row and row[0] and row[0].strip().isdigit():
        sl_no = row[0].strip()
        description = row[1].strip() if len(row) > 1 and row[1] else ""
        hsn = row[3].strip() if len(row) > 3 and row[3] else ""
        rate = row[5].strip() if len(row) > 5 and row[5] else ""
        amount = row[6].strip() if len(row) > 6 and row[6] else ""

        item_rows.append({
            ThreeDConstants.Constant_Sl: sl_no,
            ThreeDConstants.Constant_Description: description,
            ThreeDConstants.Constant_HSN_SAC: hsn,
            ThreeDConstants.Constant_Rate: rate,
            ThreeDConstants.Constant_Amount: amount
        })
        i += 1
    elif row and any(ThreeDConstants.Constant_Total in str(cell).upper() for cell in row):
        total_amount = row[-1].strip()
        i += 1
    elif row and any(ThreeDConstants.Constant_CGST in str(cell) or ThreeDConstants.Constant_SGST in str(cell) or ThreeDConstants.Constant_IGST in str(cell) for cell in row):
        tax_type = row[0].strip()
        amount = row[-1].strip()
        tax_rows.append({
            ThreeDConstants.Constant_Type: tax_type,
            ThreeDConstants.Constant_Rate: "",  # Not explicitly mentioned
            ThreeDConstants.Constant_Amount: amount
        })
        i += 1
    elif row and any(ThreeDConstants.Constant_Invoice_Value in str(cell).upper() for cell in row):
        total_amount = row[-1].strip()
        for cell in row:
            if ThreeDConstants.Constant_Rupees in str(cell):
                result[ThreeDConstants.Constant_SBTech_Amount_Chargeable] = cell.strip()
        i += 1
    else:
        i += 1

if item_rows:
    result[ThreeDConstants.Constant_Items] = item_rows

if tax_rows:
    result[ThreeDConstants.Constant_Taxes] = tax_rows

if total_amount:
    result[ThreeDConstants.Constant_SBTech_Total_Amt] = total_amount

# ------------------------------
# Footer: Could be enhanced if needed
# ------------------------------
# Not applicable in this file based on sample

# ------------------------------
# Authorised Signatory (Not present in this format)
# ------------------------------
result[ThreeDConstants.Constant_SBTech_Auth_Sign] = ""

# ------------------------------
# Clean and Save JSON
# ------------------------------
result = json.loads(json.dumps(result).replace(ThreeDConstants.Constant_cid299, '').replace(ThreeDConstants.Constant_u2122, "'"))

# Print JSON
print(json.dumps(result, indent=4, ensure_ascii=False))

# Save to keyvaluejson folder
output_folder = 'keyvalueMainjsonSBtech'
os.makedirs(output_folder, exist_ok=True)

output_filename = os.path.splitext(os.path.basename(input_path))[0] + '.json'
with open(os.path.join(output_folder, output_filename), 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)
