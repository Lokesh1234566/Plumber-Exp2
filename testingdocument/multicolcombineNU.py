import fitz  # PyMuPDF
import os
import re
import json

# --- Dummy column_boxes fallback if missing ---
try:
    from multicolumn import column_boxes
except ImportError:

    def column_boxes(page, footer_margin=50, no_image_text=True):
        return [page.rect]  # Use full page if no multicolumn logic


# Directories
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"
output_dir_txt = "Nutextfile"
output_dir_json = "Nujsonfile"

# Create output directories if they don't exist
os.makedirs(output_dir_txt, exist_ok=True)
os.makedirs(output_dir_json, exist_ok=True)

# Get list of PDF files starting with "nu"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("nu")
    and item.lower().endswith(".pdf")
]


# Helper extraction function
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


# MAIN LOOP FOR ALL PDFs
for pdf_path in file_names:
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_file_path = os.path.join(output_dir_txt, f"{base_filename}.txt")
    json_file_path = os.path.join(output_dir_json, f"{base_filename}.json")

    try:
        print(f"Processing: {pdf_path}")
        doc = fitz.open(pdf_path)
        full_text = ""

        for page in doc:
            bboxes = column_boxes(page, footer_margin=50, no_image_text=True)
            for rect in bboxes:
                try:
                    text = page.get_text(clip=rect, sort=True)
                    full_text += text + "\n\n"
                except Exception as e:
                    print(f"Text extraction error on page {page.number + 1}: {e}")

        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Text saved to: {txt_file_path}")

        # Reload text
        with open(txt_file_path, "r", encoding="utf-8") as f:
            text = f.read()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # -------------------------
        # Supplier Details
        # -------------------------
        supplier_details = {
            "name": extract(r"TAX INVOICE\s+(.+)", text),
            "address": extract(r"TAX INVOICE\s+.+\n(.+)", text),
            "pan": extract(r"PAN\s*:\s*(\S+)", text),
            "gstin": extract(r"GSTIN\s*(?:No)?\s*[:\-]?\s*(\S+)", text),
            "state": extract(r"STATE\s*-\s*(\w+)", text),
            "month": extract(r"MONTH\s*-\s*(\w+\s+\d{4})", text),
        }

        # -------------------------
        # Buyer Details
        # -------------------------
        buyer_details = {
            "name": extract(r"NAME\s*:\s*(.+)", text),
            "address": extract(r"NAME\s*:.+\n(.+)", text),
            "gstin": extract(r"GSTIN NO[:\-]*\s*(\S+)", text),
        }

        # -------------------------
        # Invoice Details
        # -------------------------
        invoice_details = {
            "invoice_number": extract(r"INVOICE NUMBER\s*[:\-]*\s*(\d+)", text),
            "date": extract(r"DATE\s*[:\-]*\s*(\d{2}/\d{2}/\d{4})", text),
            "period": extract(r"Period\s*[:\-]*\s*([^\n]+)", text),
        }

        # -------------------------
        # Line Items
        # -------------------------
        line_items = []
        item_pattern = re.compile(
            r"(\d{2}\.\d{2}\.\d{4})\s+(\d+)\s+([\w\s]+?)\s+(?:\S+)?\s+(\d+kg|\d+gms|\d+)\s+(\d+)\s+([\d,]+\.\d{2})"
        )

        for match in item_pattern.finditer(text):
            date, awb, dest, weight, quantity, amount = match.groups()
            line_items.append(
                {
                    "Date": date,
                    "AWB No": awb,
                    "Destination": dest.strip(),
                    "Weight": weight,
                    "Quantity": quantity,
                    "Amount": amount,
                }
            )

        # -------------------------
        # Tax Summary
        # -------------------------
        tax_summary = {
            "SAC Code": extract(r"SAC\s*CODE\s*[:\-]*\s*(\d+)", text),
            "Taxable Amount": extract(r"TAXABLE AMOUNT\s+([\d,]+\.\d{2})", text),
            "CGST %": extract(r"CGST AMOUNT\s*(\d+)%", text),
            "CGST Amount": extract(r"CGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
            "SGST %": extract(r"SGST AMOUNT\s*(\d+)%", text),
            "SGST Amount": extract(r"SGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
            "IGST %": extract(r"IGST AMOUNT\s*(\d+)%", text),
            "IGST Amount": extract(r"IGST AMOUNT\s*\d+%\s*([\d,]+\.\d{2})", text),
            "Fuel Charges": extract(r"FUEL CHARGERS\s*\d+%\s*([\d,]+\.\d{2})", text),
            "Round Off": extract(r"ROUND OFF\s*([\d,]+\.\d{2})", text),
        }

        # -------------------------
        # Totals
        # -------------------------
        totals = {
            "Total Amount": extract(r"TOTAL AMOUNT\s*([\d,]+\.\d{2})", text),
            "Invoice Amount": extract(r"INVOICE AMOUNT\s*\n([\d,]+\.\d{2})", text),
            "Total Consignment": extract(r"Total Consignment\s*[:\-]*\s*(\d+)", text),
        }

        # -------------------------
        # Amount in Words
        # -------------------------
        amount_in_words = extract(r"Amount In words\s*[:-]\s*(.+)", text)

        # -------------------------
        # Final Output
        # -------------------------
        output_data = {
            "supplier_details": supplier_details,
            "buyer_details": buyer_details,
            "invoice_details": invoice_details,
            "line_items": line_items,
            "tax_summary": tax_summary,
            "totals": totals,
            "amount_in_words": amount_in_words,
        }

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        print(f"JSON saved to: {json_file_path}\n")

    except Exception as e:
        print(f"Failed to process {pdf_path}: {e}\n")
