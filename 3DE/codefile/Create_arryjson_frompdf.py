import pdfplumber
import json 


pdf_path = "../pdf/A.pdf"
output_json_path = "../pdf/A_array.json"

extracted_tables = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            extracted_tables.append({"page_number": page_num + 1, "tables": tables})
            
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(extracted_tables, f, indent=4, ensure_ascii=False)