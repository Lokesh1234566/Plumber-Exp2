import re
import json

def parse_invoice(text):
    data = {}

    # Extract GSTINs
    seller_gstin = re.search(r'GSTIN:\s+([A-Z0-9]+)', text)
    consignee_gstin = re.search(r'Consignee GST:\s+([A-Z0-9]+)', text)

    # Seller address
    seller_address_match = re.search(r'--- Page \d+ ---\s+(.*?)\s+GSTIN:', text, re.DOTALL)
    seller_address = seller_address_match.group(1).strip().replace('\n', ' ') if seller_address_match else ""

    # Invoice number and date
    invoice_match = re.search(r'Invoice No\.\s+(\S+)\s+Date\s+([\d.]+)', text)
    invoice_number, invoice_date = invoice_match.groups() if invoice_match else ("", "")

    # Buyer name and address
    buyer_block = re.search(r'To\s+Invoice No.*?\n\s+(.*?)\n\s+(.*?)\n\s+(.*?)\n\s+(.*?)\n', text)
    buyer_lines = buyer_block.groups() if buyer_block else ("", "", "", "")
    buyer_name = buyer_lines[0].strip()
    buyer_address = " ".join(line.strip() for line in buyer_lines[1:])

    # PO details
    po_match = re.search(r'Your P\.O\. No\.\s+(\S+)\s+Date\s+([\d.]+)', text)
    po_number, po_date = po_match.groups() if po_match else ("", "")

    # Payment and delivery terms
    payment_match = re.search(r'Payment Terms:\s+(.+)', text)
    delivery_match = re.search(r'Delivery:\s+(.+)', text)
    payment_terms = payment_match.group(1).strip() if payment_match else ""
    delivery = delivery_match.group(1).strip() if delivery_match else ""

    # Extract product lines
    product_lines = []
    product_table = re.findall(
        r'\d+\s+(.*?)\s+(\d{8})\s+(\d+)\s+([\d.]+)\s+([\d.]+)', text
    )
    for p in product_table:
        product_lines.append({
            "description": p[0].strip(),
            "hsn": p[1].strip(),
            "quantity": int(p[2]),
            "unit_price": float(p[3]),
            "amount": float(p[4])
        })

    # Tax values
    cgst = re.search(r'CGST\s+\d+%\s+([\d.]+)', text)
    sgst = re.search(r'SGST\s+\d+%\s+([\d.]+)', text)
    igst = re.search(r'IGST\s+\d+%\s+([\d.]+)', text)

    taxes = []
    if cgst:
        taxes.append({"type": "cgst", "rate": "9%", "cgst_amount": float(cgst.group(1))})
    if sgst:
        taxes.append({"type": "sgst", "rate": "9%", "sgst_amount": float(sgst.group(1))})
    if igst:
        taxes.append({"type": "igst", "rate": "18%", "igst_amount": float(igst.group(1))})

    # Total amount
    total_match = re.search(r'TOTAL INVOICE VALUE.*?([\d,.]+)', text)
    total_amount = float(total_match.group(1).replace(",", "")) if total_match else 0.0

    # Extract bank details (if any)
    bank_match = re.search(r'Bank Details.*?Account Name\s*:\s*(.*?)\n\s*Account No\s*:\s*(.*?)\n\s*Bank Name\s*:\s*(.*?)\n\s*Branch & IFSC Code\s*:\s*(.*?)(?:\n|$)', text, re.DOTALL)
    if bank_match:
        bank_details = {
            "account_name": bank_match.group(1).strip(),
            "account_no": bank_match.group(2).strip(),
            "bank_name": bank_match.group(3).strip(),
            "ifsc": bank_match.group(4).strip()
        }
    else:
        bank_details = {}

    # Compile final JSON
    data["seller"] = {
        "name": "S.B.TECHNOLOGIES",
        "address": seller_address,
        "gstin": seller_gstin.group(1) if seller_gstin else ""
    }
    data["buyer"] = {
        "name": buyer_name,
        "address": buyer_address,
        "gstin": consignee_gstin.group(1) if consignee_gstin else ""
    }
    data["invoice"] = {
        "number": invoice_number,
        "date": invoice_date,
        "our_dc_no": "",
        "our_dc_date": "",
        "your_dc_no": "",
        "your_dc_date": "",
        "po_number": po_number,
        "po_date": po_date,
        "payment_terms": payment_terms,
        "delivery": delivery
    }
    data["items"] = product_lines
    data["taxes"] = taxes
    data["total_amount"] = total_amount
    data["bank_details"] = bank_details

    return data

# Example usage
if __name__ == "__main__":
    with open("../textoutput/sb_tech_2.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    result = parse_invoice(text)
    print(json.dumps(result, indent=2))
