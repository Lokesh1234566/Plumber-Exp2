import fitz  # PyMuPDF
import os
import re
import json

# --- Dummy column_boxes fallback if missing ---
try:
    from multicolumn import column_boxes
except ImportError:

    def column_boxes(page, footer_margin=50, no_image_text=True):
        return [page.rect]  # Use full page as fallback


# ------------------------------------------------

# Directories
input_dir = "E:\\Working_Docling_Project\\testingdocument\\allinvoices"
output_dir_txt = "LPLtextfile"
output_dir_json = "LPLjsonfile"

# Create output directories if they don't exist
os.makedirs(output_dir_txt, exist_ok=True)
os.makedirs(output_dir_json, exist_ok=True)

# Get list of PDF files starting with "Inf" or "inf"
file_names = [
    os.path.join(input_dir, item)
    for item in os.listdir(input_dir)
    if os.path.isfile(os.path.join(input_dir, item))
    and item.lower().startswith("lsp")  # lowercase check
    and item.lower().endswith(".pdf")
]


# Helper extraction function
def extract(pattern, source, default=""):
    match = re.search(pattern, source, re.MULTILINE)
    return match.group(1).strip() if match else default


# -----------------------------
# MAIN LOOP FOR ALL PDFs
# -----------------------------
for pdf_path in file_names:
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_file_path = os.path.join(output_dir_txt, f"{base_filename}.txt")
    json_file_path = os.path.join(output_dir_json, f"{base_filename}.json")

    try:
        print(f"Processing: {pdf_path}")
        doc = fitz.open(pdf_path)
        full_text = ""

        # Extracting text using column_boxes (or full page fallback)
        for page in doc:
            bboxes = column_boxes(page, footer_margin=50, no_image_text=True)
            for rect in bboxes:
                try:
                    text = page.get_text(clip=rect, sort=True)
                    full_text += text + "\n\n"
                except Exception as e:
                    print(f"Text extraction error on page {page.number + 1}: {e}")

        # Save .txt file
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Text saved to: {txt_file_path}")

        # --- Begin Data Parsing ---
        with open(txt_file_path, "r", encoding="utf-8") as f:
            text = f.read()

        lines = [line.strip() for line in text.splitlines()]

        supplier_details = {
            "name": extract(r"^(.*?)\n", text),
            "address": extract(r"^[^\n]+\n(.+?)\nGSTIN/UIN", text).replace("\n", ", "),
            "phone": extract(r"Ph NO[:\s]*(.+)", text),
            "cin": extract(r"CIN[:\s]*(.+)", text),
            "gstin_uin": extract(r"GSTIN/UIN[:\s]*(\S+)", text),
            "state_name": extract(r"State Name\s*:\s*(.+?),\s*Code\s*:\s*\d+", text),
            "state_code": extract(r"State Name\s*:\s*.+?,\s*Code\s*:\s*(\d+)", text),
            "contact": extract(r"Contact\s*:\s*(.+)", text),
            "email": extract(r"E-Mail\s*:\s*(.+)", text),
            "website": extract(r"E-Mail\s*:.+\n(\S+)", text),
        }

        # -------------------------
        # Buyer Details
        # -------------------------
        buyer_name = extract(r"Buyer\n([^\n]+)", text)
        buyer_address = extract(
            rf"Buyer\n{re.escape(buyer_name)}\n(.+\n.+\n.+)", text, ""
        ).replace("\n", ", ")

        buyer_details = {
            "name": buyer_name,
            "address": buyer_address,
            "gstin_uin": extract(r"GSTIN/UIN\s*:\s*(\S+)", text),
            "state_name": extract(r"State Name\s*:\s*(.+?), Code\s*:\s*\d+", text),
            "state_code": extract(r"State Name\s*:\s*.+?, Code\s*:\s*(\d+)", text),
            "place_of_supply": extract(r"Place of Supply\s*:\s*(.+)", text),
        }

        # -------------------------
        # Invoice Details
        # -------------------------
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

        invoice_details = {}
        for i, line in enumerate(lines):
            if line.strip() in invoice_keys:
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                key = line.strip().rstrip(".")
                invoice_details[key] = (
                    next_line.strip()
                    if next_line.strip() and next_line.strip() not in invoice_keys
                    else ""
                )

        # -------------------------
        # Line Items
        # -------------------------
        line_items = []
        i = 0
        sl_no = 1
        while i < len(lines):
            line = lines[i].strip()
            if re.match(r"^\d+\s+Supply of Prototype Parts", line) or re.match(
                r"^\d+\s+Accounting Services", line
            ):
                parts = re.split(r"\s{2,}", line)
                description = parts[1] if len(parts) > 1 else ""
                hsn = parts[2] if len(parts) > 2 else ""
                rate = parts[-2] if len(parts) > 4 else ""
                amount = parts[-1] if len(parts) > 3 else ""

                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line and not re.match(r"^\d+\s+", next_line):
                    description += " " + next_line

                line_items.append(
                    {
                        "SL No": sl_no,
                        "Description of Goods": description,
                        "HSN/SAC": hsn,
                        "Rate": rate,
                        "per": "",
                        "Disc. %": "",
                        "Amount": amount,
                    }
                )
                sl_no += 1
                i += 2
            else:
                i += 1

        # -------------------------
        # Tax Summary (CGST/SGST or IGST)
        # -------------------------
        tax_summary = []
        for match in re.finditer(
            r"(CGST|SGST|IGST)\s+(\d+\s*%)\s+([\d,]+\.\d{2})", text
        ):
            tax_summary.append(
                {
                    "Tax Type": match.group(1),
                    "Rate": match.group(2),
                    "Amount": match.group(3),
                }
            )

        # -------------------------
        # Totals
        # -------------------------
        total_amount = extract(r"Total\s+\S+\s+([\u20B9Rs\.\s]*[\d,]+\.\d{2})", text)

        totals = {"Total Amount": total_amount}

        # -------------------------
        # Amount Chargeable in Words
        # -------------------------
        amount_chargeable_words = extract(
            r"Amount Chargeable \(in words\).*?\n(.*)", text
        )

        # -------------------------
        # Bank Details
        # -------------------------
        bank_name = extract(r"Bank Name\s*:\s*(.+)", text)
        account_number = extract(r"A/c No\.\s*:\s*(\d+)", text)
        branch_ifsc = extract(r"Branch & IFS Code\s*:\s*(.+)", text)

        bank_details = {
            "Bank Name": bank_name,
            "Account Number": account_number,
            "Branch_IFSC": branch_ifsc,
        }

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
            "amount_chargeable_in_words": amount_chargeable_words,
            "bank_details": bank_details,
        }

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)
        print(f"JSON saved to: {json_file_path}\n")

    except Exception as e:
        print(f"Failed to process {pdf_path}: {e}\n")
