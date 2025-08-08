import fitz  # PyMuPDF
import os
import re
import streamlit as st
from multicolumn import column_boxes  # Ensure this is implemented and available

# Set your input PDF directory
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Collect all PDF files starting with "sar"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("sar")
    and item.lower().endswith(".pdf")
]


# --- Helper Function ---
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


# --- PDF Processor Function ---
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
        "address": ", ".join(lines[1:4]) if len(lines) > 3 else "",
        "gstin_uin": extract(r"GSTIN/UIN:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code", text),
        "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
        "email": extract(r"E[-\s]?Mail\s*:\s*(\S+)", text),
    }

    # --- Buyer Details ---
    buyer_index = lines.index("Buyer") if "Buyer" in lines else -1
    buyer_address = (
        ", ".join(
            [
                lines[buyer_index + 1] if buyer_index + 1 < len(lines) else "",
                lines[buyer_index + 2] if buyer_index + 2 < len(lines) else "",
            ]
        )
        if buyer_index != -1
        else ""
    )

    buyer_details = {
        "name": "Irillic Pvt. Ltd.",
        "address": buyer_address,
        "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
        "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code", text),
        "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
        "place_of_supply": extract(r"Place of Supply\s*:\s*(.+)", text),
        "contact_person": extract(r"Contact person\s*:\s*(.+)", text),
        "contact": extract(r"Contact\s*:\s*(\S+)", text),
    }

    # --- Invoice Details ---
    invoice_labels = [
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
        label.replace(":", "").replace("’", "'").strip(): "" for label in invoice_labels
    }

    for i in range(len(lines) - 1):
        key = lines[i].strip().replace(":", "").replace("’", "'")
        val = lines[i + 1].strip()
        if (
            key in invoice_details
            and val not in invoice_labels
            and not val.startswith("Sl ")
        ):
            invoice_details[key] = val

    # --- Line Items ---
    line_items = []
    i = 0
    while i < len(lines):
        match = re.match(
            r"^(\d+)\s+([A-Za-z\s&()\-]+)\s+(\d{6,8})\s+(\d+)\s*%\s+(\d+)\s+([A-Za-z]+)\s+(\d+)\s+([A-Za-z]+)\s+([\d,]+\.\d{2})",
            lines[i],
        )
        if match:
            sl_no, desc, hsn, gst_rate, qty_val, qty_unit, rate, per, amount = (
                match.groups()
            )
            if i + 1 < len(lines) and not lines[i + 1].startswith(tuple("1234567890")):
                desc += " " + lines[i + 1].strip()
                i += 1
            line_items.append(
                {
                    "Sl No": sl_no,
                    "Description of Goods": desc.strip(),
                    "HSN/SAC": hsn,
                    "GST Rate": gst_rate + "%",
                    "Quantity": f"{qty_val} {qty_unit}",
                    "Rate": rate,
                    "per": per,
                    "Amount": amount,
                }
            )
        i += 1

    # --- Tax Summary ---
    tax_summary = {
        "CGST Amount": extract(r"CGST\s+([\d,.]+)", text),
        "SGST Amount": extract(r"SGST\s+([\d,.]+)", text),
    }

    # --- HSN Summary ---
    hsn_summary = []
    hsn_pattern = re.compile(
        r"(\d{6,8})\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+(\d+)%\s+([\d,.]+)\s+([\d,.]+)"
    )
    for match in hsn_pattern.findall(text):
        hsn_summary.append(
            {
                "HSN/SAC": match[0],
                "Taxable Value": match[1],
                "Central Tax Rate": match[2] + "%",
                "Central Tax Amount": match[3],
                "State Tax Rate": match[4] + "%",
                "State Tax Amount": match[5],
                "Total Tax Amount": match[6],
            }
        )

    # --- Bank Details ---
    bank_details = {
        "Bank Name": extract(r"Bank Name\s*:\s*(.+)", text),
        "Account Number": extract(r"A/c No\.?\s*:\s*(\d+)", text),
        "Branch & IFSC": extract(r"Branch & IFS Code\s*:\s*(.+)", text),
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
