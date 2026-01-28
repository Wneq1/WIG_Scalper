# Importujemy niezbędne biblioteki
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from bs4 import BeautifulSoup

def fetch_gpw_data(url, output_file="gpw_portfolio.html", verbose=True):
    """
    Simulates a browser to fetch the GPW Benchmark page and saves the HTML.
    Then parses it to extract portfolio data.
    """
    if verbose:
        print(f"Connecting to {url} using Edge...")

    options = Options()
    # options.add_argument("--headless") # Commented out for debugging
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        driver = webdriver.Edge(options=options)
        driver.get(url)

        # Wait for potential cookie consent
        try:
            # GPW Benchmark often has a simple cookie banner or none that blocks content directly.
            # We wait a bit just in case.
            time.sleep(5) 
            
            # Example cookie clicking logic (adjust selector if needed)
            # cookie_btn = driver.find_element(By.ID, "cookie-accept")
            # cookie_btn.click()
        except Exception as e:
            if verbose:
                print(f"Cookie handling note: {e}")

        # Wait for the table data to load. It might be dynamic.
        time.sleep(5) 

        html = driver.page_source
        
        # Save HTML logic removed or kept optional? 
        # User wants the data mainly. I'll keep saving for debug but maybe to a temp path or current dir.
        # Let's write to current dir as requested.
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
            if verbose:
                print(f"HTML saved to {output_file}")
        except Exception:
            pass
            
        return parse_gpw_portfolio(html, verbose=verbose)

    except Exception as e:
        print(f"Error fetching GPW data: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def parse_gpw_portfolio(html_content, verbose=False):
    """
    Parses the HTML to extract Ticker, Name, and Share %.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    data = []

    # Identifying the table. 
    # Strategy: Find all tables, look for one with 'Udzial' or similar headers.
    tables = soup.find_all('table')
    
    target_table = None
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if verbose:
            print(f"DEBUG Headers found: {headers}")
        
        # Check for keywords like "ISIN", "Nazwa", "Udział" in headers
        if any("Udzia" in h for h in headers) or any("Nazwa" in h for h in headers):
            target_table = table
            break
            
    if not target_table:
        print("Could not find the portfolio table.")
        return []

    # Iterate rows
    rows = target_table.find_all('tr')
    for row in rows[1:]: # Skip header
        cols = row.find_all('td')
        if len(cols) >= 5: # We expect at least 5 cols based on debug output
            col_texts = [c.get_text(strip=True) for c in cols]
            
            # Mapping based on previous observation:
            # 0: Name/Ticker (e.g. 'ACAUTOGAZ')
            # 1: ISIN (e.g. 'PLACSA000014')
            # 4: Share % (e.g. '0,512')
            
            name = col_texts[0]
            isin = col_texts[1]
            share_str = col_texts[4].replace(',', '.')
            try:
                share = float(share_str)
            except:
                share = 0.0
                
            entry = {
                'ticker': name, # Using name as ticker for now
                'name': name,
                'isin': isin,
                'share': share
            }
            data.append(entry)

    return data