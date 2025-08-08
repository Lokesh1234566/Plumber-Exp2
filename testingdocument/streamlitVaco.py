import fitz  # PyMuPDF
import os
import re
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works

# --- Set Directory ---
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Get PDF files starting with "sb"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("vac")
    and item.lower().endswith(".pdf")
]


# --- Helper function ---
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


# --- Process PDF File ---
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
                print(f"Error on page {page.number + 1}: {e}")

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    text = "\n".join(lines)

    # --- Supplier Details ---
    supplier_details = {
        "name": "",
        "address": "",
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", text),
        "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
        "email": extract(r"E-Mail\s*:\s*(.+)", text),
    }

    gstin_index = next((i for i, line in enumerate(lines) if "GSTIN/UIN" in line), None)
    if gstin_index is not None:
        block = lines[max(0, gstin_index - 6) : gstin_index]
        block = [line.strip() for line in block if line.strip()]
        name_candidates = [
            line
            for line in block
            if re.search(r"(Vasanth|Vaco|and Co|Chartered)", line, re.IGNORECASE)
        ]
        if name_candidates:
            supplier_details["name"] = name_candidates[0]
            name_index = block.index(name_candidates[0])
            address_lines = block[name_index + 1 :]
            supplier_details["address"] = ", ".join(address_lines).strip()

    # --- Buyer Details ---
    buyer_details = {
        "name": extract(r"Buyer\s*\n([^\n]+)", text),
        "address": extract(r"Buyer\s*\n[^\n]+\n(.+\n.+\n.+)", text).replace("\n", ", "),
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", text),
        "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", text),
    }

    # --- Invoice Details ---
    invoice_keys = [
        "Invoice No.",
        "Delivery Note",
        "Supplier's Ref.",
        "Buyer's Order No.",
        "Despatch Document No.",
        "Despatched through",
        "Dated",
        "Mode/Terms of Payment",
        "Other Reference(s)",
        "Delivery Note Date",
        "Destination",
        "Terms of Delivery",
    ]

    invoice_details = {key.replace(".", "").strip(): "" for key in invoice_keys}
    for i in range(len(lines) - 1):
        current_line = lines[i].strip()
        next_line = lines[i + 1].strip()
        for key in invoice_keys:
            clean_key = key.replace(".", "").strip()
            if key in current_line and invoice_details[clean_key] == "":
                invoice_details[clean_key] = next_line if next_line else ""

    # --- Line Items ---
    line_items = []
    item_pattern = re.compile(r"^(\d+)\s+(.*?)\s{2,}(\d{6,8})?\s{2,}([\d,]+\.\d{2})$")
    i = 0
    while i < len(lines):
        match = item_pattern.match(lines[i])
        if match:
            sl_no = match.group(1)
            description = match.group(2).strip()
            hsn_sac = match.group(3) or ""
            amount = match.group(4)

            if re.search(r"(CGST|SGST|IGST)", description, re.IGNORECASE):
                i += 1
                continue

            full_desc = [description]
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if (
                    item_pattern.match(lines[j])
                    or next_line.startswith("Total")
                    or re.match(r"^\d+\s+(CGST|SGST|IGST)", next_line)
                ):
                    break
                if next_line:
                    full_desc.append(next_line)
                j += 1

            line_items.append(
                {
                    "Sl No": sl_no,
                    "Particulars": " ".join(full_desc),
                    "HSN/SAC": hsn_sac,
                    "Rate": "",
                    "per": "",
                    "Amount": amount,
                }
            )
            i = j
        else:
            i += 1

    # --- Tax Summary ---
    tax_summary = {
        "CGST Rate (%)": "",
        "CGST Amount": "",
        "SGST Rate (%)": "",
        "SGST Amount": "",
    }
    for line in lines:
        if "CGST" in line:
            tax_summary["CGST Rate (%)"] = extract(r"CGST\s+(\d+)\s*%", line)
            tax_summary["CGST Amount"] = extract(r"(\d{1,3}(?:,\d{3})*\.\d{2})", line)
        elif "SGST" in line:
            tax_summary["SGST Rate (%)"] = extract(r"SGST\s+(\d+)\s*%", line)
            tax_summary["SGST Amount"] = extract(r"(\d{1,3}(?:,\d{3})*\.\d{2})", line)

    # --- Totals ---
    totals = {"Total Amount": extract(r"Total\s+₹?\s*([\d,]+\.\d{2})", text)}

    # --- Amount in Words ---
    amount_chargeable_words = ""
    for i, line in enumerate(lines):
        if "Amount Chargeable (in words)" in line:
            amount_chargeable_words = lines[i + 1].strip() if i + 1 < len(lines) else ""
            break

    # --- Bank Details ---
    bank_details = {
        "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
        "Account Number": extract(r"A/c\s*No\.?\s*:\s*(\d+)", text),
        "Branch_IFSC": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", text),
    }

    # --- Final Output ---
    output_data = {
        "supplier_details": supplier_details,
        "buyer_details": buyer_details,
        "invoice_details": invoice_details,
        "line_items": line_items,
        "tax_summary": tax_summary,
        "totals": totals,
        "amount_chargeable_in_words": amount_chargeable_words,
        "hsn_summary": [],  # Optional
        "bank_details": bank_details,
    }

    return full_text, output_data


# --- Streamlit UI ---
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
