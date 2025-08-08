import markdown
from bs4 import BeautifulSoup

def get_table_rows_from_md(md_filepath):
        """
        Extracts table rows from a Markdown file.

        Args:
            md_filepath (str): The path to the Markdown file.

        Returns:
            list: A list of lists, where each inner list represents a table row.
        """
        with open(md_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['tables'])

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the table
        table = soup.find('table')
        if not table:
            return []  # No table found

        rows_data = []
        # Extract header row
        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        rows_data.append(headers)

        # Extract data rows
        for row in table.find('tbody').find_all('tr'):
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            rows_data.append(cols)

        return rows_data

    # Example usage:
md_file = '../mdfile/Infiniti1213.md'
table_rows = get_table_rows_from_md(md_file)

if table_rows:
        print("Table Rows:")
        for row in table_rows:
            print(row)
else:
        print("No table found or file error.")