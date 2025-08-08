import fitz  # PyMuPDF
import os
import re
import json
import streamlit as st

# --- Dummy column_boxes fallback ---
try:
    from multicolumn import column_boxes
except ImportError:

    def column_boxes(page, footer_margin=50, no_image_text=True):
        return [page.rect]  # Fallback to full page


# Directory to read Infiniti PDFs from
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Get all filenames starting with "inf"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("inf")
    and item.lower().endswith(".pdf")
]


# Helper function
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


def process_infiniti_pdf(pdf_path):
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

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    # Supplier Details
    supplier_details = {
        "name": extract(r"^(INFINITI ENGINEERS PRIVATE LIMITED)", full_text),
        "address": extract(
            r"INFINITI ENGINEERS PRIVATE LIMITED\n(.+?\n.+?\n.+?)\n", full_text
        ).replace("\n", ", "),
        "phone": extract(r"PH:\s*(.+)", full_text),
        "pan": extract(r"PAN NO:\s*(\S+)", full_text),
        "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", full_text),
        "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", full_text),
        "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", full_text),
        "email": extract(r"E-Mail\s*:\s*(.+)", full_text),
    }

    # Buyer Details
    buyer_name = extract(r"Buyer\s*\n([^\n]+)", full_text)
    buyer_address = extract(
        rf"Buyer\s*\n{re.escape(buyer_name)}\n(.+\n.+\n.+)", full_text, ""
    ).replace("\n", ", ")
    buyer_details = {
        "name": buyer_name,
        "address": buyer_address,
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", full_text),
        "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", full_text),
        "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", full_text),
    }

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

    invoice_details = {}
    for i, line in enumerate(lines):
        if line in invoice_keys:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if next_line.strip() in invoice_keys or not next_line.strip():
                invoice_details[line.rstrip(".")] = ""
            else:
                invoice_details[line.rstrip(".")] = next_line.strip()

    # Line Items
    line_items = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "RENTAL OF LAPTOP" in line:
            try:
                header = lines[i]
                hsn = re.search(r"(\d{8})", header)
                qty = re.search(r"(\d+)\s+NOS", header)
                rate = re.search(r"NOS\.\s+([\d,]+\.\d{2})", header)
                amount = re.findall(r"([\d,]+\.\d{2})", header)
                per = re.search(r"\b(NOS)\b", header)

                desc_block_lines = []
                for offset in range(1, 6):
                    if i + offset < len(lines):
                        desc_block_lines.append(lines[i + offset].strip())
                full_desc = " ".join(desc_block_lines).strip()

                line_items.append(
                    {
                        "Description of Goods": full_desc,
                        "HSN/SAC": hsn.group(1) if hsn else "",
                        "Quantity": qty.group(1) if qty else "",
                        "Rate": rate.group(1) if rate else "",
                        "per": per.group(1) if per else "",
                        "Disc. %": "",
                        "Amount": amount[-1] if amount else "",
                    }
                )
                i += 6
            except:
                i += 1
        else:
            i += 1

    # Tax Summary
    tax_summary = {
        "SGST Rate (%)": extract(r"SGST\s*@\s*(\d+)%", full_text),
        "SGST Amount": extract(
            r"SGST\s*@\s*\d+%\s*\d+\s*%\s*([\d,]+\.\d{2})", full_text
        ),
        "CGST Rate (%)": extract(r"CGST\s*@\s*(\d+)%", full_text),
        "CGST Amount": extract(
            r"CGST\s*@\s*\d+%\s*\d+\s*%\s*([\d,]+\.\d{2})", full_text
        ),
    }

    # Totals
    totals = {
        "Total Quantity": extract(r"Total\s+(\d+)\s+NOS", full_text),
        "Total Amount": extract(
            r"Total\s+\d+\s+NOS\.\s+[^\d]*([\d,]+\.\d{2})", full_text
        ),
    }

    # Amount in words
    amount_chargeable_words = ""
    for i, line in enumerate(lines):
        if "Amount Chargeable (in words)" in line:
            amount_chargeable_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
            break

    # HSN Summary
    hsn_summary = []
    hsn_blocks = re.findall(
        r"(\d{6,8})\s+([\d,]+\.\d{2})\s+([\d.]+)%\s+([\d,]+\.\d{2})\s+([\d.]+)%\s+([\d,]+\.\d{2})",
        full_text,
    )
    for hsn, taxable_val, cgst_rate, cgst_amt, sgst_rate, sgst_amt in hsn_blocks:
        total_tax_amt = f"{(float(cgst_amt.replace(',', '')) + float(sgst_amt.replace(',', ''))):,.2f}"
        hsn_summary.append(
            {
                "HSN/SAC": hsn,
                "Taxable Value": taxable_val,
                "Central Tax Rate": f"{cgst_rate}%",
                "Central Tax Amount": cgst_amt,
                "State Tax Rate": f"{sgst_rate}%",
                "State Tax Amount": sgst_amt,
                "Total Tax Amount": total_tax_amt,
            }
        )

    # Bank details
    bank_line = extract(r"Bank Name\s*:\s*(.+)", full_text)
    bank_name, account_number = "", ""
    if bank_line:
        match = re.match(r"(.+?)\s*\((\d{10,20})\)", bank_line)
        if match:
            bank_name, account_number = match.groups()
        else:
            bank_name = bank_line

    branch_ifsc = extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", full_text)
    if not branch_ifsc:
        branch = extract(r"Branch\s*:\s*(.+)", full_text)
        ifsc = extract(r"IFSC\s*:\s*(\S+)", full_text)
        branch_ifsc = f"{branch}, {ifsc}" if branch and ifsc else ifsc

    bank_details = {
        "Bank Name": bank_name,
        "Account Number": account_number,
        "Branch_IFSC": branch_ifsc,
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
        "bank_details": bank_details,
    }

    return full_text, output_data


# -------------- Streamlit UI --------------

st.set_page_config(layout="wide")
st.title("📑 Infiniti Invoice Extractor")

col1, col2 = st.columns([1, 2])

with col1:
    selected_file = st.selectbox("Select an Infiniti PDF file", options=file_names)

with col2:
    if selected_file:
        st.success(f"Selected file: {os.path.basename(selected_file)}")
        extracted_text, extracted_json = process_infiniti_pdf(selected_file)

        st.subheader("📜 Extracted Text")
        st.text_area("Text Output", extracted_text, height=300)

        st.subheader("📦 Structured JSON")
        st.json(extracted_json)
