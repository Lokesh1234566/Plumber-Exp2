import fitz  # PyMuPDF
import os
import re
import streamlit as st
from multicolumn import column_boxes  # Ensure this exists and works

# --- Directories ---
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"

# Get list of PDF files starting with "3de"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("sb")
    and item.lower().endswith(".pdf")
]


# --- Helper function ---
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


# --- PDF Processor ---
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
                print(
                    f"Error extracting text from rectangle on page {page.number + 1}: {e}"
                )

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    text = "\n".join(lines)  # reused for regex searches

    # --- Supplier Details ---
    address_lines = []
    for line in lines:
        address_lines.append(line)
        if len(address_lines) == 2:
            break
    cleaned_address = ", ".join(address_lines)

    supplier_details = {
        "name": "",
        "address": cleaned_address,
        "gstin_uin": extract(r"GSTIN[:\s]+(\S+)", text),
        "phone": extract(r"PH:\+?([\d\s]+)", text),
    }

    # --- Buyer Details ---
    buyer_name = ""
    buyer_address_lines = []
    invoice_keywords = [
        "Our DC No.",
        "Your P.O.",
        "GST",
        "Invoice No.",
        "Your DC No.",
        "Date",
    ]

    for i, line in enumerate(lines):
        if line.startswith("To"):
            name_index = i + 1
            buyer_name = lines[name_index].strip() if name_index < len(lines) else ""

            k = name_index - 1
            while k > 0:
                prev_line = lines[k].strip()
                if not prev_line or "To" in prev_line:
                    break
                buyer_address_lines.insert(0, prev_line)
                k -= 1

            for j in range(name_index + 1, name_index + 6):
                if j >= len(lines):
                    break
                current_line = lines[j].strip()
                if any(keyword in current_line for keyword in invoice_keywords):
                    for keyword in invoice_keywords:
                        if keyword in current_line:
                            current_line = current_line.split(keyword)[0].strip()
                if current_line:
                    buyer_address_lines.append(current_line)
            break

    buyer_details = {
        "name": buyer_name,
        "address": ", ".join(buyer_address_lines),
        "gstin_uin": extract(r"Consignee GST:\s*(\S+)", text),
    }

    # --- Invoice Details ---
    invoice_details = {
        "Invoice No": "",
        "Invoice Date": "",
        "Our DC No": "",
        "Our DC Date": "",
        "Your DC No": "",
        "Your DC Date": "",
        "PO No": "",
        "PO Date": "",
        "Payment Terms": "",
        "Delivery": "",
    }

    inline_patterns = {
        "Invoice No": r"Invoice No\.?\s*[:\-]?\s*(\S+)",
        "Invoice Date": r"Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        "PO No": r"P\.?O\.? No\.?\s*[:\-]?\s*(\S+)",
        "PO Date": r"P\.?O\.? No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        "Payment Terms": r"Payment Terms\s*[:\-]?\s*(.*)",
        "Delivery": r"Delivery\s*[:\-]?\s*(.*)",
        "Our DC No": r"Our DC No\.?\s*[:\-]?\s*(\S+)",
        "Our DC Date": r"Our DC No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        "Your DC No": r"Your DC No\.?\s*[:\-]?\s*(\S+)",
        "Your DC Date": r"Your DC No.*?Date\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
    }

    for key, pattern in inline_patterns.items():
        invoice_details[key] = extract(pattern, text)

    # Fallback key-value on next line
    labels = {
        "Invoice No.": "Invoice No",
        "Date": ["Invoice Date", "PO Date", "Our DC Date", "Your DC Date"],
        "Our DC No.": "Our DC No",
        "Your DC No.": "Your DC No",
        "Your P.O. No.": "PO No",
        "Payment Terms": "Payment Terms",
        "Delivery": "Delivery",
    }

    seen_date_fields = set()

    for i in range(len(lines) - 1):
        current = lines[i]
        next_line = lines[i + 1]

        if current in labels:
            keys = labels[current]
            if isinstance(keys, list):
                for date_key in keys:
                    if (
                        not invoice_details[date_key]
                        and date_key not in seen_date_fields
                    ):
                        if next_line.lower() != "date":
                            invoice_details[date_key] = next_line
                            seen_date_fields.add(date_key)
                        break
            else:
                if not invoice_details[keys] and next_line.lower() != "date":
                    invoice_details[keys] = next_line

    for key in invoice_details:
        if invoice_details[key].lower() == "date":
            invoice_details[key] = ""

    # --- Line Items ---
    line_items = []
    line_pattern = re.compile(
        r"^\s*(\d+)\s+(.*?)\s+(\d{6,8})\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)",
        re.MULTILINE,
    )

    for match in line_pattern.finditer(text):
        sl_no, desc, hsn, qty, unit_price, amount = match.groups()
        line_items.append(
            {
                "Sl No": sl_no,
                "Description": desc.strip(),
                "HSN/SAC": hsn,
                "Quantity": int(qty),
                "Unit Price": float(unit_price.replace(",", "")),
                "Amount": float(amount.replace(",", "")),
            }
        )

    # --- Tax Summary ---
    tax_summary = {
        "CGST 9%": extract(r"CGST\s+9%\s+([\d,]+\.\d{2})", text),
        "SGST 9%": extract(r"SGST\s+9%\s+([\d,]+\.\d{2})", text),
        "IGST 18%": extract(r"IGST\s+18%\s+([\d,]+\.\d{2})", text),
    }

    # --- Totals ---
    total_amount = extract(r"TOTAL\s+(\d{5,7}\.\d{2})", text)
    amount_chargeable_words = extract(
        r"TOTAL INVOICE VALUE\s+Rupees\s+(.*?)\s+\d", text
    )

    totals = {
        "Total Amount (before tax)": sum(item["Amount"] for item in line_items),
        "CGST": (
            float(tax_summary["CGST 9%"].replace(",", ""))
            if tax_summary["CGST 9%"]
            else 0.0
        ),
        "SGST": (
            float(tax_summary["SGST 9%"].replace(",", ""))
            if tax_summary["SGST 9%"]
            else 0.0
        ),
        "IGST": (
            float(tax_summary["IGST 18%"].replace(",", ""))
            if tax_summary["IGST 18%"]
            else 0.0
        ),
        "Total Invoice Value": (
            float(total_amount.replace(",", "")) if total_amount else 0.0
        ),
    }

    # --- Bank Details ---
    bank_details = {
        "Bank Name": extract(r"Bank Name\s*:\s*(.*)", text) or "N/A",
        "A/c No": extract(r"A/c No\.?\s*[:\-]?\s*(\d+)", text) or "N/A",
        "Branch & IFS Code": extract(r"Branch & IFS Code\s*:\s*(.*)", text) or "N/A",
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
