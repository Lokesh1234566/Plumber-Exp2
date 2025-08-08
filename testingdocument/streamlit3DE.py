import fitz  # PyMuPDF
import os
import re
import json
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works

# Directories
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Get list of PDF files starting with "3de"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item)) and item.lower().startswith("3de") and item.lower().endswith(".pdf")
]

# Helper functions
def extract(pattern, source, default=''):
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
                print(f"Error extracting text from rectangle on page {page.number + 1}: {e}")

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    # Supplier Details
    supplier_details = {
        "name": lines[0].strip(),
        "address": ', '.join(lines[1:6]).strip(),
        "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", full_text),
        "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", full_text),
        "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", full_text),
        "email": extract(r"E-Mail\s*:\s*(.+)", full_text)
    }

    # Buyer Details
    buyer_details = {
        "name": extract(r"Buyer\s*\n([^\n]+)", full_text),
        "address": extract(r"Buyer\s*\n[^\n]+\n(.+\n.+\n.+)", full_text).replace('\n', ', '),
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", full_text),
        "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", full_text),
        "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", full_text)
    }

    # Invoice Details
    invoice_keys = [
        "Invoice No.", "Delivery Note", "Supplier’s Ref.", "Buyer’s Order No.",
        "Despatch Document No.", "Despatched through", "Dated",
        "Mode/Terms of Payment", "Other Reference(s)", "Delivery Note Date",
        "Destination", "Terms of Delivery"
    ]

    invoice_details = {}
    for i, line in enumerate(lines):
        if line.strip() in invoice_keys:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            invoice_details[line.rstrip('.')] = next_line.strip() if next_line.strip() not in invoice_keys else ""

    # Line Items
    line_items = []
    sl_counter = 1

    for i in range(len(lines)):
        if re.match(r"^\d+\s+Supply of Prototype Parts", lines[i]):
            header_line = lines[i]
            desc_line = lines[i + 1] if i + 1 < len(lines) else ""

            hsn = extract(r"(\d{8})", header_line)
            qty = extract(r"(\d+)\s+Nos", header_line)
            rate = extract(r"Nos\.\s+([\d,]+\.\d{2})", header_line)
            amount = extract(r"([\d,]+\.\d{2})$", header_line)
            gst_rate = extract(r"(\d{1,2})\s*%", header_line)

            full_desc = "Supply of Prototype Parts " + desc_line.strip()

            line_items.append({
                "Sl No": str(sl_counter),
                "Description of Goods": full_desc,
                "HSN/SAC": hsn,
                "Quantity": qty,
                "Rate": rate,
                "per": "Nos",
                "Disc. %": "",
                "Amount": amount,
                "GST Rate": f"{gst_rate}%" if gst_rate else ""
            })

            sl_counter += 1

    totals = {
        "Total Quantity": extract(r"Total\s+(\d+)\s+Nos", full_text),
        "Total Amount": extract(r"Total\s+\d+\s+Nos\.\s+[^\d]*([\d,]+\.\d{2})", full_text)
    }

    tax_summary = {
        "IGST Rate (%)": extract(r"(\d+)%\s+([\d,]+\.\d{2})", full_text),
        "IGST Amount": extract(r"\d+%\s+([\d,]+\.\d{2})", full_text)
    }

    hsn_summary = []
    hsn_blocks = re.findall(
        r"(\d{6,8})\s+([\d,]+\.\d{2})\s+(\d+)%\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
        full_text
    )
    for hsn, taxable_val, rate, amount, total in hsn_blocks:
        hsn_summary.append({
            "HSN/SAC": hsn,
            "Taxable Value": taxable_val,
            "Integrated Tax Rate": f"{rate}%",
            "Integrated Tax Amount": amount,
            "Total Tax Amount": total
        })

    amount_chargeable_words = ""
    for i, line in enumerate(lines):
        if "Amount Chargeable (in words)" in line:
            amount_chargeable_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
            break

    bank_details = {
        "Bank Name": extract(r"Bank Name\s*:\s*(.+)", full_text),
        "Account Number": extract(r"A/c\s*No\.?\s*:\s*(\d+)", full_text),
        "Branch_IFSC": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", full_text)
    }

    output_data = {
        "supplier_details": supplier_details,
        "buyer_details": buyer_details,
        "invoice_details": invoice_details,
        "line_items": line_items,
        "tax_summary": tax_summary,
        "totals": totals,
        "amount_chargeable_in_words": amount_chargeable_words,
        "hsn_summary": hsn_summary,
        "bank_details": bank_details
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
