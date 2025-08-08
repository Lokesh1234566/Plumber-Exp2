import os


directory_path = "./allinvoices"  # Replace with the actual path
file_names = []

for item in os.listdir(directory_path):
    item_path = os.path.join(directory_path, item)
    if os.path.isfile(item_path):
        if item.startswith("3de"):
            file_names.append(item)

print(file_names)
# mylist = file_names
# # check letter
# b = '3'

# res = [i for i in mylist if i[0].lower() == b.lower()]
# print(res)
