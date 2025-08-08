import fitz  # PyMuPDF
import os
import re
import json
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works

# Directory path for invoice PDFs
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Fetch PDF files starting with "nu"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("nu")
    and item.lower().endswith(".pdf")
]


# Helper function to extract regex pattern from source
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        bboxes = column_boxes(page, footer_margin=50, no_image_text=True)
        for rect in bboxes:
            try:
                text = page.get_text(clip=rect, sort=True)
                full_text += text + "\n\n"
            except Exception as e:
                print(f"Error extracting text from page {page.number + 1}: {e}")

    text = full_text
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    # Supplier Details
    supplier_details = {
        "name": extract(r"TAX INVOICE\s+(.+)", text),
        "address": extract(r"TAX INVOICE\s+.+\n(.+)", text),
        "pan": extract(r"PAN\s*:\s*(\S+)", text),
        "gstin": extract(r"GSTIN\s*(?:No)?\s*[:\-]?\s*(\S+)", text),
        "state": extract(r"STATE\s*-\s*(\w+)", text),
        "month": extract(r"MONTH\s*-\s*(\w+\s+\d{4})", text),
    }

    # Buyer Details
    buyer_details = {
        "name": extract(r"NAME\s*:\s*(.+)", text),
        "address": extract(r"NAME\s*:.+\n(.+)", text),
        "gstin": extract(r"GSTIN NO[:\-]*\s*(\S+)", text),
    }

    # Invoice Details
    invoice_details = {
        "invoice_number": extract(r"INVOICE NUMBER\s*[:\-]*\s*(\d+)", text),
        "date": extract(r"DATE\s*[:\-]*\s*(\d{2}/\d{2}/\d{4})", text),
        "period": extract(r"Period\s*[:\-]*\s*([^\n]+)", text),
    }

    # Line Items
    line_items = []
    item_pattern = re.compile(
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d+)\s+([\w\s]+?)\s+(?:\S+)?\s+(\d+(?:kg|gms)?)\s+(\d+)\s+([\d,]+\.\d{2})"
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

    # Tax Summary
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

    # Totals
    totals = {
        "Total Amount": extract(r"TOTAL AMOUNT\s*([\d,]+\.\d{2})", text),
        "Invoice Amount": extract(r"INVOICE AMOUNT\s*\n([\d,]+\.\d{2})", text),
        "Total Consignment": extract(r"Total Consignment\s*[:\-]*\s*(\d+)", text),
    }

    # Amount in Words
    amount_in_words = extract(r"Amount In words\s*[:-]\s*(.+)", text)

    # Final Output JSON
    output_data = {
        "supplier_details": supplier_details,
        "buyer_details": buyer_details,
        "invoice_details": invoice_details,
        "line_items": line_items,
        "tax_summary": tax_summary,
        "totals": totals,
        "amount_in_words": amount_in_words,
    }

    return full_text, output_data


# Streamlit UI
st.set_page_config(layout="wide")
st.title("📄 PDF Invoice Extractor")

col1, col2 = st.columns([1, 2])

with col1:
    selected_file = st.selectbox("Select a PDF file", options=file_names)

with col2:
    if selected_file:
        st.success(f"Selected: {os.path.basename(selected_file)}")
        text_content, json_data = process_pdf(selected_file)

        st.subheader("📄 Extracted Text")
        st.text_area("Full Extracted Text", value=text_content, height=300)

        st.subheader("🧾 JSON Output")
        st.json(json_data)
