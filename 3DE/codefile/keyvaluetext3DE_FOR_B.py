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
input_path = Path("../arrayjson/B_array.json")

# --- Load JSON data ---
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}
file_read = open("../codefile/B.md", "r")

    # asking the user to enter the string to be 
    # searched
text="Destination"
lengthofdestination = 11
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
        #   see if value beside destination ,Destination 123456
            if(len(line.strip() )> 11):
                print(line)
                s1=line.replace("Destination","")
                destinationValue =s1
                print(destinationValue)
        
            print ("Line No %d - %s" % (idx, line))   
            if idx<line_count-1:   
             next_line = lines[idx + 1]
            print ("Next Line No %d - %s" % (idx+1, next_line))
            if  textNextLineDestinationShouldNotBe not in next_line:
             destinationValue+=str(next_line)
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
# Extract Key-Value Pairs in Column 5
# ------------------------------
table = data[0]['tables'][0]
table_rows = data[0]['tables'][0]
for row in table_rows:
    #print("table row" + str(row))
    if len(row) > 4 and row[4]:
        cell = row[4]
        if '\n' in cell:
            parts = cell.split('\n', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            result[key] = value
        else:
            result[cell.strip()] = ""





result["Destination"] = destinationValue.replace("\n", " ")
result["Terms of Delivery"] = termsofDeliveryValue.replace("\n", " ")
# ------------------------------
# Extract and Merge Item Rows
# ------------------------------
item_rows = []
header_row = None
start_idx = None
rows = table
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


# Output JSON
output_dir = Path("../keyvaluemainjson")
output_dir.mkdir(parents=True, exist_ok=True)

output_file_path = output_dir / input_path.name # Uses the same filename

with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Output saved to: {output_file_path}")

