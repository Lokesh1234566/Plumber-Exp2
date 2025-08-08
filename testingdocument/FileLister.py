import os

folder_path = './allinvoices'  # Replace with the actual path to your folder

try:
    for item_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item_name)
        if os.path.isfile(full_path):  # Check if the item is a file
            print(item_name)
            
            # my_list.sort()
except FileNotFoundError:
    print(f"Error: The folder '{folder_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")