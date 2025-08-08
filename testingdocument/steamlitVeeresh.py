import fitz  # PyMuPDF
import os
import re
import json
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works

# Directories
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Get list of PDF files starting with "veer"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("veer")
    and item.lower().endswith(".pdf")
]


# Helper functions
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

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    text = full_text  # For using in regex extraction

    # Supplier Details
    supplier_details = {
        "name": lines[0],
        "address": ", ".join(lines[1:3]),
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?),", text),
        "state_code": extract(r"Code\s*:\s*(\d+)", text),
        "contact": extract(r"Contact\s*:\s*(.+)", text),
    }

    # Buyer Details
    buyer_details = {}
    for i, line in enumerate(lines):
        if line.lower() == "customer":
            name = lines[i + 1]
            address = lines[i + 2]
            gstin = ""
            state_name = ""
            state_code = ""

            for j in range(i + 3, min(i + 8, len(lines))):
                if "GSTIN/UIN" in lines[j]:
                    gstin = extract(r"GSTIN/UIN\s*:\s*(\S+)", lines[j])
                if "State Name" in lines[j]:
                    state_name = extract(r"State Name\s*:\s*(.+?),", lines[j])
                    state_code = extract(r"Code\s*:\s*(\d+)", lines[j])

            buyer_details = {
                "name": name,
                "address": address,
                "gstin_uin": gstin,
                "state_name": state_name,
                "state_code": state_code,
            }
            break

    # Invoice Details
    invoice_keys = [
        "Invoice No.",
        "Delivery Note",
        "Supplier’s Ref.",
        "Buyer’s Order No.",
        "Despatch Document No.",
        "Despatched through",
        "Dated",
        "Mode/Terms of Payment",
        "Other Reference(s)",
        "Delivery Note Date",
        "Destination",
        "Terms of Delivery",
    ]

    invoice_details = {
        key.replace("’", "'").replace(".", "").strip(): "" for key in invoice_keys
    }

    seen_keys = set()
    i = 0
    while i < len(lines) - 1:
        current_line = lines[i].strip()
        next_line = lines[i + 1].strip()

        for raw_key in invoice_keys:
            cleaned_key = raw_key.replace("’", "'").replace(".", "").strip()
            if cleaned_key in seen_keys:
                continue

            if current_line == raw_key:
                if next_line not in invoice_keys and not next_line.startswith("Sl "):
                    invoice_details[cleaned_key] = next_line
                else:
                    invoice_details[cleaned_key] = ""
                seen_keys.add(cleaned_key)
                break
        i += 1

    # Line Items
    line_items = []
    item_pattern = re.compile(
        r"^(\d+)\s+(.*?)\s{2,}(\d+)\s+([A-Z]+)\s+([\d,]+\.\d{2})\s+[A-Z]+\s+([\d,]+\.\d{2})$"
    )

    for line in lines:
        match = item_pattern.match(line)
        if match:
            sl_no = match.group(1)
            description = match.group(2)
            quantity_number = match.group(3)
            quantity_unit = match.group(4)
            rate = match.group(5)
            amount = match.group(6)

            line_items.append(
                {
                    "Sl No": sl_no,
                    "Particulars": description,
                    "HSN/SAC": "",
                    "Quantity": f"{quantity_number} {quantity_unit}",
                    "Rate": rate,
                    "per": quantity_unit,
                    "Amount": amount,
                }
            )

    # Tax Summary
    tax_summary = {
        "CGST Rate (%)": "",
        "CGST Amount": "",
        "SGST Rate (%)": "",
        "SGST Amount": "",
    }

    for line in lines:
        if re.search(
            r"\d{1,3}(,\d{3})*\.\d{2}.*\d+%\s+\d{1,3}(,\d{3})*\.\d{2}.*\d+%\s+\d{1,3}(,\d{3})*\.\d{2}",
            line,
        ):
            match = re.search(
                r"(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d+)%\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d+)%\s+(\d{1,3}(?:,\d{3})*\.\d{2})",
                line,
            )
            if match:
                tax_summary["CGST Rate (%)"] = match.group(2)
                tax_summary["CGST Amount"] = match.group(3)
                tax_summary["SGST Rate (%)"] = match.group(4)
                tax_summary["SGST Amount"] = match.group(5)
                break

    # HSN Summary
    hsn_summary = []
    for line in lines:
        line = line.strip()
        match = re.search(
            r"(\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d+%)\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d+%)\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})",
            line,
        )
        if match:
            hsn_summary.append(
                {
                    "HSN/SAC": "",
                    "Taxable Value": match.group(1),
                    "CGST Rate": match.group(2),
                    "CGST Amount": match.group(3),
                    "SGST Rate": match.group(4),
                    "SGST Amount": match.group(5),
                    "Total Tax Amount": match.group(6),
                }
            )

    # Totals
    total_qty = extract(r"Total\s+(\d+\s+[A-Z]+)", text)
    total_amount = extract(r"Total.*?([\d,]+\.\d{2})", text)
    totals = {"Total Quantity": total_qty, "Total Amount": total_amount}

    # Amount in Words
    amount_chargeable_words = ""
    for i, line in enumerate(lines):
        if "Amount Chargeable (in words)" in line:
            amount_chargeable_words = lines[i + 1].strip()
            break

    # Bank Details
    bank_details = {
        "Bank Name": "",
        "Branch": "",
        "IFSC Code": "",
        "Account Number": "",
    }

    for line in lines:
        line = line.strip()
        if re.search(r"\bBank Name\b", line, re.IGNORECASE):
            bank_details["Bank Name"] = extract(r"Bank Name\s*:\s*(.*)", line)
        elif (
            re.search(r"\bBank\b", line, re.IGNORECASE)
            and not bank_details["Bank Name"]
        ):
            bank_details["Bank Name"] = extract(r"Bank\s*:\s*(.*)", line)

        if re.search(r"IFSC\s*Code", line, re.IGNORECASE):
            bank_details["IFSC Code"] = extract(r"IFSC\s*Code\s*[:\-]?\s*(\S+)", line)

        if re.search(r"Branch", line, re.IGNORECASE):
            if "Branch & IFSC" in line:
                bank_details["Branch"] = extract(
                    r"Branch\s*&\s*IFSC\s*Code\s*:\s*(.*?)\s+\S+$", line
                )
            else:
                bank_details["Branch"] = extract(r"Branch\s*:\s*(.*)", line)

        if re.search(r"A/c\s*No", line, re.IGNORECASE):
            bank_details["Account Number"] = extract(
                r"A/c\s*No\.?\s*[:\-]?\s*(\d+)", line
            )
        elif re.search(r"Account\s*No", line, re.IGNORECASE):
            bank_details["Account Number"] = extract(
                r"Account\s*No\.?\s*[:\-]?\s*(\d+)", line
            )

    # Final JSON
    output_data = {
        "supplier_details": supplier_details,
        "buyer_details": buyer_details,
        "invoice_details": invoice_details,
        "line_items": line_items,
        "tax_summary": tax_summary,
        "hsn_summary": hsn_summary,
        "totals": totals,
        "amount_chargeable_in_words": amount_chargeable_words,
        "bank_details": bank_details,
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
