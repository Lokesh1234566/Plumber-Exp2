# from docling.document_converter import DocumentConverter

# # For a local file
# source_path = "../pdf/Bedit.pdf"  # Replace with your local document path

# # Create a converter and convert the file
# converter = DocumentConverter()
# result = converter.convert(source_path)

# # Access the converted document
# document = result.document

# # Export to HTML format
# # md_output =  result.document.export_to_markdown()

# # # Save the output to an HTML file
# # output_path = "./B1edit.md"
# # with open(output_path, "w", encoding="utf-8") as f:
# #     f.write(md_output)

# # print(f"HTML saved to: {output_path}")

# # Export to HTML format
# outputText =  result.document.export_to_dict()
# print(outputText)
# # Save the output to an HTML file
# output_path1 = "./B1edit.txt"
# with open(output_path1, "w", encoding="utf-8") as f:
#     f.write(outputText)



from docling.document_converter import DocumentConverter

# For a local file
source_path = "../pdf/Aedit1.pdf"  # Replace with your local document path

# Create a converter and convert the file
converter = DocumentConverter()
result = converter.convert(source_path)

# Access the converted document
document = result.document

# Export to HTML format
md_output =  result.document.export_to_markdown()

# Save the output to an HTML file
output_path = "./Aedit1.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(md_output)

print(f"HTML saved to: {output_path}")
