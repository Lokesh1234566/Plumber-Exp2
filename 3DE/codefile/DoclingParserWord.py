
import docling
from docling_core.types.doc.page import TextCellUnit
from docling_parse.pdf_parser import DoclingPdfParser, PdfDocument
from docling_core.types.doc.document import DoclingDocument
from docling.document_converter import DocumentConverter
import json
import pandas as pd
parser = DoclingPdfParser()
pdf_doc: PdfDocument = parser.load(
    path_or_stream="../pdf/Bedit.pdf"
)

for page_no, pred_page in pdf_doc.iterate_pages():

    # iterate over the word-cells
   for word in pred_page.iterate_cells(unit_type= TextCellUnit.WORD):
          # iterate over the word-cells  
       print(word.rect, ": ", word.text)
       #print( word.text)

        # create a PIL image with the char cells
     #img = pred_page.render_as_image(cell_unit=TextCellUnit.CHAR)
     #img.show()

#for page_no, pred_page in pdf_doc.iterate_pages():
   #pred_page.save_as_json("C:\\Allfiles\\APred.json")
    # iterate over the word-cells
   # for word in pred_page.iterate_cells(unit_type=TextCellUnit.WORD):
          # iterate over the word-cells  
     #   print(word.rect, ": ", word.text)
      #  print( word.text)

