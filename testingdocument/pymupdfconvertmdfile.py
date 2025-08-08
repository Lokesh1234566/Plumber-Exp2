import pymupdf
import os
from multicolumn import column_boxes

# Define paths
pdf_path = "./Infiniti Bill 1336_01.pdf"
output_dir = "./output"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Open the PDF document
doc = pymupdf.open(pdf_path)

# Choose the page you want to process (page 1 in this case, index 1)
page = doc[1]

# Extract column-wise bounding boxes
bboxes = column_boxes(page, footer_margin=50, no_image_text=True)

# Initialize an empty string to collect all extracted text
full_text = ""

# Extract text from each column and append
for rect in bboxes:
    text = page.get_text(clip=rect, sort=True)
    full_text += text + "\n\n"

# Define output file name (you can customize this)
output_file = os.path.join(output_dir, "Infiniti_Bill_1336_01_page_2.txt")

# Save the text to the file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Text extracted and saved to {output_file}")
