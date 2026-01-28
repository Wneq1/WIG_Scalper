from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time

def fetch_gpw_data():
    """
    Fetches the list of companies from the GPW Benchmark website.
    Returns:
        list: A list of dicts with 'ticker', 'share', and 'name'. Returns empty list on failure.
    """
    edge_options = Options()
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    # edge_options.add_argument("--headless") # Commented out to see the browser, uncomment if desired
    edge_options.add_argument("start-maximized")
    edge_options.add_argument("disable-infobars")

    driver = None
    companies = []
    
    try:
        try:
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
        except Exception:
            # Fallback to default edge driver in path
            try:
                driver = webdriver.Edge(options=edge_options)
            except Exception as e:
                print(f"Error initializing Edge driver: {e}")
                return []

        url = "https://gpwbenchmark.pl/karta-indeksu?isin=PL9999999060#Portfolio"
        print(f"Fetching data from: {url}")
        driver.get(url)
        
        # Wait for the table to load
        wait = WebDriverWait(driver, 20)
        table_present = wait.until(EC.presence_of_element_located((By.ID, "footable")))
        
        # Give a little extra time for rows to populate if needed
        time.sleep(5)
        
        rows = table_present.find_elements(By.CSS_SELECTOR, "tbody tr")
        print(f"Found {len(rows)} rows in the table.")
        
        for idx, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # DEBUG: Print first row to see column structure
                if idx == 0:
                    print(f"\n=== DEBUG: First row has {len(cells)} columns ===")
                    for i, cell in enumerate(cells):
                        print(f"Column {i}: '{cell.text.strip()}'")
                    print("=" * 50 + "\n")
                
                if len(cells) >= 6:  # Ensure we have enough columns
                    # Column 0: Ticker (Instrument)
                    ticker = cells[0].text.strip()
                    
                    # Column 4: Udział w portfelu (%) - CORRECTED from column 5
                    share_text = cells[4].text.strip()
                    
                    if ticker:
                        # Parse share percentage (e.g., "4,908" -> 4.908)
                        try:
                            share_value = float(share_text.replace(',', '.'))
                        except (ValueError, AttributeError):
                            share_value = 0.0
                            print(f"Warning: Could not parse share for {ticker}: '{share_text}'")
                        
                        companies.append({
                            'ticker': ticker,
                            'share': share_value,
                            'name': ticker
                        })
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

    except Exception as e:
        print(f"An error occurred during fetching: {e}")
    finally:
        if driver:
            driver.quit()
            
    return companies

if __name__ == "__main__":
    # Test run
    data = fetch_gpw_data()
    print(f"Fetched {len(data)} companies:")
    print(data)
