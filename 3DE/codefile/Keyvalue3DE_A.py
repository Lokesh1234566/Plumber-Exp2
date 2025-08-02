import json
import os

# ------------------------------
# Load JSON File
# ------------------------------
input_file_path = '../pdf/A_array.json'
with open(input_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

result = {}

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
table_rows = data[0]['tables'][0]
for row in table_rows:
    if len(row) > 4 and row[4]:
        cell = row[4]
        if '\n' in cell:
            parts = cell.split('\n', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            result[key] = value
        else:
            result[cell.strip()] = ""

# ------------------------------
# Extract and Merge Item Rows
# ------------------------------
item_rows = []
header_row = None
start_idx = None

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

    for i in range(0, max_len - 1, 2):
        for j in range(2):
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

if item_rows:
    result["Items"] = item_rows

# ------------------------------
# Extract Footer Details as Key-Value Pairs (Page 2)
# ------------------------------
footer_info = {}
page2_tables = data[1]["tables"][0]

buffer = []
current_key = None

for row in page2_tables:
    for cell in row:
        if cell and isinstance(cell, str):
            text = cell.strip()

            # Match known structured fields
            if text.startswith("Amount Chargeable"):
                key, value = text.split("\n", 1)
                footer_info[key.strip(": ")] = value.strip()
            elif text.startswith("Tax Amount (in words)"):
                key, value = text.split(":", 1)
                footer_info[key.strip()] = value.strip()
            elif text.startswith("Bank Name"):
                key, value = text.split(":", 1)
                footer_info["Bank Name"] = value.strip()
            elif text.startswith("A/c No."):
                key, value = text.split(":", 1)
                footer_info["A/c No."] = value.strip()
            elif text.startswith("Branch & IFS Code"):
                key, value = text.split(":", 1)
                footer_info["Branch & IFS Code"] = value.strip()
            elif text.startswith("Declaration for"):
                current_key = "Declaration"
                buffer = []
            elif "Authorised Signatory" in text:
                if current_key == "Declaration" and buffer:
                    footer_info[current_key] = " ".join(buffer).strip()
                    current_key = None
                footer_info["Authorised Signatory"] = text.strip()
            elif current_key == "Declaration":
                buffer.append(text.strip())

if footer_info:
    result["Footer Info"] = footer_info

# ------------------------------
# Clean and Output Result
# ------------------------------
result = json.loads(json.dumps(result).replace('(cid:299)', '').replace('\u2122', "'"))

# ------------------------------
# Save Output to Folder: keyvalue3de_A
# Output filename same as input but with _output suffix
# ------------------------------
output_dir = "../keyvalue3de_A"
os.makedirs(output_dir, exist_ok=True)

input_filename = os.path.basename(input_file_path)
output_filename = os.path.splitext(input_filename)[0] + "_output.json"
output_file_path = os.path.join(output_dir, output_filename)

with open(output_file_path, "w", encoding="utf-8") as out_file:
    json.dump(result, out_file, indent=4, ensure_ascii=False)

# Optional: print result
print(json.dumps(result, indent=4))
