import pdfplumber
import pandas as pd
# from pdfplumber.utils import extract_text, get_bbox_overlap, obj_to_bbox
# def process_pdf(pdf_path):
#     pdf = pdfplumber.open(pdf_path)
#     all_text = []
#     for page in pdf.pages:
#         filtered_page = page
#         chars = filtered_page.chars
#         for table in page.find_tables():
#             first_table_char = page.crop(table.bbox).chars[0]
#             filtered_page = filtered_page.filter(lambda obj: 
#                 get_bbox_overlap(obj_to_bbox(obj), table.bbox) is None
#             )
#             chars = filtered_page.chars
#             df = pd.DataFrame(table.extract())
#             df.columns = df.iloc[0]
#             markdown = df.drop(0).to_markdown(index=False)
#             chars.append(first_table_char | {"text": markdown})
#         page_text = extract_text(chars, layout=True)
#         all_text.append(page_text)
#     pdf.close()
#     return "\n".join(all_text)


# Path to your PDF file
pdf_path = r"../pdf/Aedit3.pdf"
# extracted_text = process_pdf(pdf_path)
# print(extracted_text)


all_text = ""
with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"  # Add a newline for readability between pages
        print(all_text)
        
        
lineCounter=1
with pdfplumber.open(pdf_path) as pdf:
       for page in pdf.pages:
        lines = page.extract_text_lines()

        print(f"Extracted lines from {pdf_path}, Page {lineCounter}")
        lineCounter=lineCounter+1
        for line in lines:
            #print(f"  - Text: {line['text']}, Top: {line['top']:.2f}")
            print(f"  - Text: {line['text']}")