import requests
from bs4 import BeautifulSoup

def inspect_gpw_table():
    """
    Pobiera i analizuje strukturę tabeli GPW
    """
    url = "https://www.gpw.pl/wskazniki-spolki"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables")
        
        if tables:
            main_table = tables[0]
            
            # Get headers
            headers_row = main_table.find('thead')
            if headers_row:
                headers = headers_row.find_all('th')
                print(f"\nTable headers ({len(headers)} columns):")
                for i, header in enumerate(headers):
                    print(f"  Column {i}: '{header.get_text(strip=True)}'")
            
            # Get first few rows
            tbody = main_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')[:5]
                print(f"\nFirst {len(rows)} data rows:")
                for row_idx, row in enumerate(rows):
                    cells = row.find_all('td')
                    print(f"\n  Row {row_idx} ({len(cells)} cells):")
                    for cell_idx, cell in enumerate(cells):
                        print(f"    Column {cell_idx}: '{cell.get_text(strip=True)}'")
        
        # Save HTML for inspection
        with open('gpw_table_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nSaved HTML to gpw_table_debug.html")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_gpw_table()
