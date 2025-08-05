from docling_parse.pdf_parser import DoclingPdfParser, PdfDocument
import pymupdf
from multi_column import column_boxes
import os

# Input file path
input_pdf_path = "../pdf/sb_tech_2.pdf"

# Initialize parser and load PDF
parser = DoclingPdfParser()
pdf_doc: PdfDocument = parser.load(path_or_stream=input_pdf_path)

# Open the same PDF with pymupdf for extraction
doc = pymupdf.open(input_pdf_path)

# Generate output file name based on input file
input_filename = os.path.basename(input_pdf_path)           # "sb_tech_1.pdf"
filename_without_ext = os.path.splitext(input_filename)[0]  # "sb_tech_1"
output_dir = "../textoutput"
output_file = os.path.join(output_dir, f"{filename_without_ext}.txt")  # "../textoutput/sb_tech_1.txt"

# Make sure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Write extracted text to file
with open(output_file, "w", encoding="utf-8") as f:
    for page_num, page in enumerate(doc, start=1):
        bboxes = column_boxes(page, footer_margin=50, no_image_text=True)
        f.write(f"--- Page {page_num} ---\n")
        for rect in bboxes:
            text = page.get_text(clip=rect, sort=True)
            f.write(text + "\n")
        f.write("-" * 80 + "\n")

print(f"✅ Output written to: {output_file}")
