import fitz  # PyMuPDF
import os
import re
import json


with open("../testingdocument/Vimatextfile/vima3ya_58_07.txt", "r") as file:
    content = file.read()
    print(content)
    contentLength = len(content)

    index = content.index("bank_details")
    # print("Despatch Document No")
    print("bank_details", index)
    index2 = content[index : contentLength - index]
    print("bank_details", index2)

    with open("../testingdocument/Vimajsonfile/vima3ya_58_07.json") as fp:
        datadict = json.load(fp)
    for key, value in datadict.items():
        print(f"{key}: {value}")

    for item in datadict["bank_details"]:
        print(item)

    # for item in datadict["supplier_details"]:
    #     print(item)
    # print(datadict[item])
