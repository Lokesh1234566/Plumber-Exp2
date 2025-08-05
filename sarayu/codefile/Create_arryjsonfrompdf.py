import pdfplumber
import json

pdf_path = "../pdf/sarayu_74_06.pdf"
output_json_path = "../arrayjson/sarayu_74_06.json"

def replace_none_with_empty_string(obj):
    if isinstance(obj, list):
        return [replace_none_with_empty_string(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: replace_none_with_empty_string(value) for key, value in obj.items()}
    elif obj is None:
        return ""
    else:
        return obj

extracted_tables = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            cleaned_tables = replace_none_with_empty_string(tables)
            extracted_tables.append({"page_number": page_num + 1, "tables": cleaned_tables})

with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(extracted_tables, f, indent=4, ensure_ascii=False)
