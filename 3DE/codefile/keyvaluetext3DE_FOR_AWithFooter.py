import json
import ThreeDConstants

# ------------------------------
# Load JSON File
# ------------------------------
with open('../arrayjson/A_array.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = {}
file_read = open("../mdfile/Aedit.md", "r")

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
# ------------------------------
# Extract Footer Details as Structured Key-Value Pairs (Page 2)
# ------------------------------
footer_info = {}
bank_details = {}
buffer = []
current_section = None

page2_tables = data[1]["tables"][0]
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
                       print(itemSplit[0])
                       if(itemSplit[0]).startswith("Bank Name") and (len(itemSplit))>1:
                        bank_details["Bank Name"] =itemSplit[1]
                       if(itemSplit[0]).startswith("A/c No.") and (len(itemSplit))>1:
                        bank_details["A/c No."] =itemSplit[1]
                       if(itemSplit[0]).startswith("Branch & IFS Code") and (len(itemSplit))>1:
                        bank_details["Branch & IFS Code"] =itemSplit[1]
                       if(itemSplit[0]).startswith("Declaration for") :
                        bank_details["Declaration"] =itemSplit[0]
                    #key, val = text.split("\n") 
                    #key, val = text.split("\n") 
                   
                    footer_info["Tax Amount (in words)"] = val.strip()

            elif text.startswith("Bank Name"):
                key, val = text.split(":", 1)
                bank_details["Bank Name"] = val.strip()

            elif text.startswith("A/c No."):
                key, val = text.split(":", 1)
                bank_details["A/c No."] = val.strip()

            elif text.startswith("Branch & IFS Code"):
                key, val = text.split(":", 1)
                bank_details["Branch & IFS Code"] = val.strip()

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

# Print JSON
print(json.dumps(result, indent=4, ensure_ascii=False))

