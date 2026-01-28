
import json
import os
import requests
import time
from bs4 import BeautifulSoup
from database import init_db, get_sector_from_db, save_sector_to_db

# Upewniamy się, że tabela w bazie jest utworzona
init_db()

# Statyczna lista jako "seed" dla spółek, których API nie wykrywa
STATIC_SECTORS = {
    # Finanse / Bankowość / Inwestycje
    "MENNICA": "Finanse",
    "MCI": "Finanse",
    "QUERCUS": "Finanse",
    "VOTUM": "Finanse",
    "BOS": "Bankowość",
    "XTB": "Finanse",

    # Nieruchomości / Deweloperzy
    "ECHO": "Nieruchomości",
    "MLPGROUP": "Nieruchomości",
    "MURAPOL": "Nieruchomości",
    "ARCHICOM": "Nieruchomości",
    "ATAL": "Nieruchomości",
    "DEVELIA": "Nieruchomości",
    "GTC": "Nieruchomości",
    "PHN": "Nieruchomości",

    # Budownictwo
    "TORPOL": "Budownictwo",
    "POLIMEXMS": "Budownictwo",
    "FERRO": "Budownictwo",
    "DECORA": "Budownictwo",
    "ELEKTROTI": "Budownictwo",
    "SELENAFM": "Budownictwo",
    "UNIBEP": "Budownictwo",
    "MOSTALZAB": "Budownictwo",
    "ERBUD": "Budownictwo",
    "ONDE": "Budownictwo",
    "MCR": "Budownictwo", 
    "PEKABEX": "Budownictwo",
    "TIM": "Budownictwo",
    "SNIEZKA": "Budownictwo",  # Farby i lakiery

    # Przemysł / Produkcja
    "APATOR": "Przemysł",
    "STALPROD": "Przemysł",
    "GRENEVIA": "Przemysł",
    "BORYSZEW": "Przemysł",
    "FORTE": "Przemysł",
    "AMICA": "Przemysł",
    "COGNOR": "Przemysł",
    "ARCTIC": "Przemysł",
    "WIELTON": "Przemysł",
    "MANGATA": "Przemysł",
    "PCCROKITA": "Chemia",
    "CLNPHARMA": "Medycyna",  # Pharma
    
    # Spożywczy
    "WAWEL": "Spożywczy",
    "TARCZYNSKI": "Spożywczy",
    "AMBRA": "Spożywczy",
    "ASTARTA": "Spożywczy",

    # IT / Technologia
    "CREOTECH": "Technologia",
    "VIGOPHOTN": "Technologia",
    "XTPL": "Technologia",
    "ASSECOBS": "IT",
    "COMP": "IT",
    "SHOPER": "IT",
    "DATAWALK": "IT",
    "SYGNITY": "IT",
    "AILLERON": "IT",
    "R22": "IT",

    # Medycyna / Bio
    "SELVITA": "Medycyna",
    "RYVU": "Medycyna",
    "BIOCELTIX": "Medycyna",
    "CAPTORTX": "Medycyna",
    "SCPFL": "Medycyna",
    "MEDICALG": "Medycyna",
    "SNTVERSE": "Medycyna",
    "BIOTON": "Medycyna",
    "MERCATOR": "Medycyna",
    "MABION": "Medycyna",
    "MOLECURE": "Medycyna",

    # Handel / E-commerce
    "OPONEO.PL": "Handel",
    "TOYA": "Handel",
    "DADELO": "Handel",
    "WITTCHEN": "Odzież",
    "VRG": "Odzież",
    "AGORA": "Media",  # Wydawnictwo/Media
    
    # Usługi / Inne
    "ENTER": "Usługi",
    "STALEXP": "Usługi",
    "RAINBOW": "Usługi",
    "BENEFIT": "Usługi", 
    
    # Gaming
    "PLAYWAY": "Gaming",
    "BLOOBER": "Gaming",
    "CREEPYJAR": "Gaming",
    "CIGAMES": "Gaming",
    "11BIT": "Gaming",
    "PCFGROUP": "Gaming",

    # Energia / Paliwa / Górnictwo
    "KOGENERA": "Energetyka",
    "ZEPAK": "Energetyka",
    "UNIMOT": "Paliwa",
    "COLUMBUS": "Energetyka",
    "MLSYSTEM": "Energetyka",
    "BOGDANKA": "Górnictwo",
    "BUMECH": "Górnictwo",
    "GREENX": "Górnictwo",
    "ACAUTOGAZ": "Paliwa",
    
    # Motoryzacja
    "SANOK": "Motoryzacja",
    "ARLEN": "Motoryzacja",
}

# Mapowanie indeksów sektorowych GPW na czytelne nazwy
INDEX_TO_SECTOR = {
    "WIG-BANKI": "Bankowość",
    "WIG-BUDOW": "Budownictwo",
    "WIG-CHEMIA": "Chemia",
    "WIG-ENERG": "Energetyka",
    "WIG-GORNIC": "Górnictwo",
    "WIG-GRY": "Gaming",
    "WIG-GAMES": "Gaming",
    "WIG-INFORMAT": "IT",
    "WIG-INFO": "IT",
    "WIG-LEKI": "Medycyna",
    "WIG-MEDIA": "Media",
    "WIG-MOTORYZ": "Motoryzacja",
    "WIG-MOTO": "Motoryzacja",
    "WIG-NIERUCH": "Nieruchomości",
    "WIG-ODZIEZ": "Odzież",
    "WIG-PALIWA": "Paliwa",
    "WIG-SPOZYW": "Spożywczy",
    "WIG-TELKOM": "Telekomunikacja",
    "WIG-ESG": "Inne" # Zbyt ogólne
}

def fetch_sector_live(ticker):
    """
    Pobiera stronę Biznesradar dla danego tickera i szuka przynależności do indeksów sektorowych.
    To jest ta 'Część AI' - dynamiczne wnioskowanie z sieci.
    """
    url = f"https://www.biznesradar.pl/notowania/{ticker}"
    try:
        # Udajemy przeglądarkę
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Szukamy sekcji "Udział w indeksach" lub linków zawierających "WIG-"
        # Zazwyczaj są w divie o id lub klasie, ale prościej przeszukać wszystkie linki
        links = soup.find_all("a", href=True)
        
        found_sectors = []
        
        for link in links:
            href = link['href']
            # Sprawdzamy czy link prowadzi do indeksu WIG
            if "indeks:WIG-" in href or "indeks:WIG." in href:
                # Wyciągamy nazwę indeksu np. WIG-GRY
                parts = href.split("indeks:")
                if len(parts) > 1:
                    idx_name = parts[1].split(",")[0].upper()
                    
                    # Sprawdzamy w naszej mapie
                    for key in INDEX_TO_SECTOR:
                        if key in idx_name:
                            found_sectors.append(INDEX_TO_SECTOR[key])
                            
        if found_sectors:
            # Zwracamy najczęstszy lub pierwszy (priorytet: IT, Gaming, Banki)
            # Prostym sposobem jest wzięcie pierwszego unikalnego
            return found_sectors[0]
            
        # Fallback 2: Szukamy tekstu "Sektor" w treści (jeśli indeksy zawiodą)
        # Np. "Sektor: Informatyka"
        # To wymagałoby zaawansowanego parsowania tekstu, na razie pomijamy

    except Exception as e:
        print(f"Błąd pobierania sektora dla {ticker}: {e}")
        
    return None

def get_sector(ticker):
    """
    Zwraca sektor. Priorytety:
    1. Static Map (najszybciej, nadpisuje wszystko)
    2. Baza Danych (już znane)
    3. Scraping online (AI/Live) -> Zapis do Bazy
    4. "Nieznany"
    """
    ticker = ticker.upper().strip()
    
    # 0. Static overrides (fixing issues with unidentified sectors)
    # Jeśli mamy zdefiniowane na sztywno - ufamy temu bezwarunkowo.
    if ticker in STATIC_SECTORS:
        # Zapisujemy do bazy, żeby sektor był dostępny przy kolejnym uruchomieniu
        save_sector_to_db(ticker, STATIC_SECTORS[ticker]) 
        return STATIC_SECTORS[ticker]

    # 1. Sprawdzamy w bazie danych SQLite
    db_sector = get_sector_from_db(ticker)
    if db_sector:
        return db_sector
    
    # 2. Live Scraping (tylko jeśli nie ma w bazie i nie ma w static)
    print(f"[AI] Rozpoznaję sektor dla nowej spółki: {ticker}...")
    sector = fetch_sector_live(ticker)
    
    if sector:
        print(f" -> Znaleziono: {sector}")
        save_sector_to_db(ticker, sector)
        # Małe opóźnienie żeby nie zbanowali IP przy masowym pobieraniu
        time.sleep(0.5) 
        return sector
    
    # 3. Fallback
    return "Inne / Nieznany"

def enrich_data_with_sectors(data_list):
    """
    Przebiega przez listę spółek i uzupełnia sektory.
    Wyświetla pasek postępu w konsoli.
    """
    print("\n--- [AI] Aktualizacja bazy wiedzy o sektorach (SQLite) ---")
    
    for i, company in enumerate(data_list):
        ticker = company.get('ticker')
        # Wywołanie get_sector automatycznie pobierze i zapisze do DB jeśli trzeba
        sec = get_sector(ticker)
        company['sector'] = sec
        
        if i % 20 == 0:
            print(f"Przetworzono {i}/{len(data_list)}...")
            
    print("Zakończono analizę sektorową.\n")
    return data_list
