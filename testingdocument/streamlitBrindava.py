import fitz  # PyMuPDF
import os
import re
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works


# --- Directory containing PDF files ---
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Filter PDF files starting with "bri"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("bri")
    and item.lower().endswith(".pdf")
]


# --- Helper Function for Pattern Extraction ---
def extract(pattern, source, default="", flags=0):
    match = re.search(pattern, source, re.MULTILINE | flags)
    return match.group(1).strip() if match else default


# --- Core PDF Processing ---
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
        "name": lines[0] if lines else "",
        "address": ", ".join(lines[1:5]) if len(lines) >= 5 else "",
        "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?),", text),
        "state_code": extract(r"Code\s*:\s*(\d+)", text),
        "contact": extract(r"Contact\s*:\s*(.+)", text),
        "email": extract(r"E-Mail\s*:\s*(.+)", text),
    }

    # --- Buyer Details ---
    buyer_block = extract(r"Buyer\s*(.*?)GSTIN/UIN", text, flags=re.DOTALL)
    buyer_lines = buyer_block.splitlines()

    buyer_details = {
        "name": buyer_lines[0].strip() if buyer_lines else "",
        "address": " ".join([line.strip() for line in buyer_lines[1:] if line.strip()]),
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
    }

    # --- Invoice Details ---
    invoice_labels = [
        "BRINDAVAN\\13102",
        "Delivery Note",
        "Supplier's Ref.",
        "Buyer's Order No.",
        "Despatch Document No.",
        "Despatched through",
        "Terms of Delivery",
        "Mode/Terms of Payment",
        "Other Reference(s)",
        "Dated",
        "Delivery Note Date",
        "Destination",
    ]

    clean_keys = [
        label.replace(":", "").replace("\\", "").strip() for label in invoice_labels
    ]
    invoice_details = {key: "" for key in clean_keys}

    excluded_values = [
        "",
        "Sl                Description of Goods            HSN/SAC   Part No.    Quantity     Rate     per     Amount",
    ]

    for i in range(len(lines) - 1):
        key = lines[i].strip().replace(":", "").replace("\\", "")
        val = lines[i + 1].strip()
        if key in invoice_details:
            if val not in clean_keys and val not in excluded_values:
                invoice_details[key] = val

    # Rename key for standardization
    invoice_details["Invoice No"] = invoice_details.pop("BRINDAVAN13102", "")

    # --- Line Items ---
    line_items = []
    item_pattern = re.compile(
        r"^(.+?)\s{2,}(\d{6,8})\s+(\d+)\s+([A-Za-z]+)\s+([\d,]+\.\d{2})\s+([A-Za-z]+)\s+([\d,]+\.\d{2})$"
    )

    for line in lines:
        match = item_pattern.match(line)
        if match:
            line_items.append(
                {
                    "Description of Goods": match.group(1).strip(),
                    "HSN/SAC": match.group(2),
                    "Part No": match.group(3),
                    "Quantity": f"{match.group(3)} {match.group(4)}",
                    "Rate": match.group(5),
                    "per": match.group(6),
                    "Amount": match.group(7),
                }
            )

    # --- Tax Summary ---
    tax_summary = {
        "CGST Rate (%)": extract(r"Output CGST @\s*(\d+)%", text),
        "CGST Amount": extract(r"Output CGST @\s*\d+%\s+\d+ %\s+([\d,.]+)", text),
        "SGST Rate (%)": extract(r"Output SGST @\s*(\d+)%", text),
        "SGST Amount": extract(r"Output SGST @\s*\d+%\s+\d+ %\s+([\d,.]+)", text),
    }

    # --- HSN Summary ---
    hsn_summary = []
    hsn_match = re.search(
        r"(\d{6,8})\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+([\d,.]+)",
        text,
    )
    if hsn_match:
        hsn_summary.append(
            {
                "HSN/SAC": hsn_match.group(1),
                "Taxable Value": hsn_match.group(2),
                "CGST Rate": hsn_match.group(3) + "%",
                "CGST Amount": hsn_match.group(4),
                "SGST Rate": hsn_match.group(5) + "%",
                "SGST Amount": hsn_match.group(6),
                "Total Tax Amount": hsn_match.group(7),
            }
        )

    # --- Bank Details ---
    bank_details = {
        "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
        "Account Number": extract(r"A/c No\.\s*:\s*(\d+)", text),
        "Branch & IFS Code": extract(r"Branch\s*&\s*IFS\s*Code\s*:\s*(.+)", text),
    }

    # --- Final Output ---
    output_data = {
        "supplier_details": supplier_details,
        "buyer_details": buyer_details,
        "invoice_details": invoice_details,
        "line_items": line_items,
        "tax_summary": tax_summary,
        "hsn_summary": hsn_summary,
        "bank_details": bank_details,
    }

    return text, output_data


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
