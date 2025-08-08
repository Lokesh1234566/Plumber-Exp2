import pymupdf
import os
from multicolumn import column_boxes
output_dir = "./txtfile"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

pdf_path = "./pdf/SB Tech__05.pdf"

# Extract base filename without extension
base_filename = os.path.splitext(os.path.basename(pdf_path))[0]

doc = pymupdf.open(pdf_path)
# Initialize an empty string to collect all extracted text
full_text = ""
for page in doc:
    bboxes = column_boxes(page, footer_margin=50, no_image_text=True)
    for rect in bboxes:
        text = page.get_text(clip=rect, sort=True)
      
        full_text += text + "\n\n"
        print(page.get_text(clip=rect, sort=True))
    # print("-" * 80)
    # Define output file name (you can customize this)
# output_file = os.path.join(output_dir, "Infiniti_Bill_1336_01_full.txt")
# Define output file name using input filename
output_file = os.path.join(output_dir, f"{base_filename}.txt")

# Save the text to the file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Text extracted and saved to {output_file}")
    # print("*************************")