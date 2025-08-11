import json

# ---------- CONFIG ----------
json_path = "../testingdocument/Vimajsonfile/vima3ya_212 Signed_12.json"
text_path = "../testingdocument/Vimatextfile/vima3ya_212 Signed_12.txt"
# ----------------------------

# Load JSON
with open(json_path, "r", encoding="utf-8") as fp:
    datadict = json.load(fp)

# Load text content
with open(text_path, "r", encoding="utf-8") as file:
    content = file.read()


# ---------- VALIDATION FUNCTION ----------
def validate_field(field_name, value, content):
    """Checks if value exists in content and prints result."""
    if not value:  # skip empty
        return
    if str(value).strip() in content:
        print(f"[OK] {field_name} found in text.")
    else:
        print(f"[MISMATCH] {field_name} not found in text! (Value: {value})")


# ---------- BANK DETAILS ----------
print("\n--- BANK DETAILS ---")
bank_data = datadict.get("bank_details", {})
for key, value in bank_data.items():
    validate_field(f"Bank detail '{key}'", value, content)

# ---------- SUPPLIER DETAILS ----------
print("\n--- SUPPLIER DETAILS ---")
supplier = datadict.get("supplier_details", {})
for key, value in supplier.items():
    validate_field(f"Supplier '{key}'", value, content)

# ---------- BUYER DETAILS ----------
print("\n--- BUYER DETAILS ---")
buyer = datadict.get("buyer_details", {})
for key, value in buyer.items():
    validate_field(f"Buyer '{key}'", value, content)

# ---------- INVOICE DETAILS ----------
print("\n--- INVOICE DETAILS ---")
invoice = datadict.get("invoice_details", {})
for key, value in invoice.items():
    validate_field(f"Invoice '{key}'", value, content)

# ---------- LINE ITEMS ----------
print("\n--- LINE ITEMS ---")
line_items = datadict.get("line_items", [])
for idx, item in enumerate(line_items, start=1):
    for key, value in item.items():
        validate_field(f"Line {idx} '{key}'", value, content)

# ---------- TAX SUMMARY ----------
print("\n--- TAX SUMMARY ---")
tax_summary = datadict.get("tax_summary", {})
for key, value in tax_summary.items():
    validate_field(f"Tax summary '{key}'", value, content)

# ---------- HSN SUMMARY ----------
print("\n--- HSN SUMMARY ---")
hsn_summary = datadict.get("hsn_summary", [])
for idx, item in enumerate(hsn_summary, start=1):
    for key, value in item.items():
        validate_field(f"HSN {idx} '{key}'", value, content)

print("\n Validation completed.")
