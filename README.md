# WIG sWIG80 Analyzer 📊

Aplikacja do analizy składu indeksu **sWIG80** z automatycznym pobieraniem danych z GPW Benchmark, klasyfikacją sektorową spółek oraz wizualizacją w formie wykresów kołowych.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Funkcje

- **Automatyczne pobieranie danych** z GPW Benchmark (https://gpwbenchmark.pl)
- **Inteligentne cachowanie** - dane odświeżane tylko po kwartalnych rewizjach (marzec, czerwiec, wrzesień, grudzień)
- **Klasyfikacja sektorowa** spółek z wykorzystaniem:
  - Bazy danych SQLite (cache)
  - Live scraping z BiznesRadar
  - Statycznych mapowań dla znanych przypadków
- **Wizualizacja danych**:
  - Wykres kołowy TOP spółek wg udziału w portfelu
  - Wykres kołowy podziału wg sektorów
  - Tabele z pełną listą spółek i rankingiem sektorów
- **Dark Mode** - nowoczesny ciemny motyw interfejsu

## 📸 Zrzuty ekranu

### Analiza wg Spółek
Wykres pokazuje TOP 12 spółek o największym udziale w indeksie sWIG80.

### Analiza wg Sektorów
Agregacja spółek według sektorów gospodarki (Budownictwo, IT, Nieruchomości, Medycyna, itd.).

## 🚀 Instalacja

### Wymagania
- Python 3.8+
- Microsoft Edge (dla Selenium WebDriver)
- Połączenie internetowe (do pierwszego pobrania danych)

### Instalacja zależności

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
selenium
webdriver-manager
matplotlib
requests
beautifulsoup4
```

## 💻 Użycie

### Uruchomienie aplikacji

```bash
python main.py
```

### Pierwsze uruchomienie
- Program automatycznie pobierze dane z GPW Benchmark (otworzy przeglądarkę Edge)
- Pobierze sektory dla wszystkich spółek (może potrwać 2-3 minuty)
- Zapisze dane w lokalnej bazie SQLite (`wig_data.db`)

### Kolejne uruchomienia
- Program sprawdzi, czy nastąpiła kwartalna rewizja indeksu
- Jeśli NIE - błyskawicznie wczyta dane z bazy (bez otwierania przeglądarki)
- Jeśli TAK - pobierze świeże dane i zaktualizuje bazę

## 📅 Harmonogram rewizji sWIG80

Indeks sWIG80 jest rewidowany **4 razy w roku**:
- **Trzeci piątek marca** (rewizja roczna)
- **Trzeci piątek czerwca** (korekta kwartalna)
- **Trzeci piątek września** (korekta kwartalna)
- **Trzeci piątek grudnia** (korekta kwartalna)

Program automatycznie wykrywa te daty i aktualizuje dane dzień po rewizji.

## 🏗️ Architektura

```
wig/
├── main.py                 # Główny plik aplikacji (GUI + orkiestracja)
├── fetch_gpw_debug.py      # Scraper GPW Benchmark (Selenium)
├── sectors.py              # Logika klasyfikacji sektorowej
├── database.py             # Obsługa SQLite (portfolio + sektory)
├── scheduler.py            # Logika harmonogramu rewizji
├── wig_data.db             # Baza danych SQLite (generowana automatycznie)
└── README.md               # Ten plik
```

### Moduły

#### `main.py`
- Interfejs graficzny (Tkinter + Matplotlib)
- Logika decyzyjna: cache vs. live fetch
- Wizualizacja wykresów i tabel

#### `fetch_gpw_debug.py`
- Selenium WebDriver (Edge)
- Pobieranie tabeli z GPW Benchmark
- Ekstrakcja tickerów i udziałów procentowych

#### `sectors.py`
- Klasyfikacja sektorowa spółek
- Priorytet: STATIC_SECTORS → Database → Live Scraping (BiznesRadar)
- Mapowanie indeksów WIG-* na sektory

#### `database.py`
- Tabela `companies`: ticker → sektor
- Tabela `portfolio`: ticker → udział %
- Funkcje: init, save, load, bulk upsert

#### `scheduler.py`
- Obliczanie dat rewizji (3. piątek miesiąca)
- Funkcja `should_update_portfolio()` - decyzja o aktualizacji

## 🗄️ Baza danych

### Tabela `companies`
```sql
CREATE TABLE companies (
    ticker TEXT PRIMARY KEY,
    sector TEXT,
    updated_at TIMESTAMP
);
```

### Tabela `portfolio`
```sql
CREATE TABLE portfolio (
    ticker TEXT PRIMARY KEY,
    share REAL,
    updated_at TIMESTAMP
);
```

## 🎨 Interfejs

- **Dark Mode** - ciemny motyw (tło #2b2b2b)
- **Zakładki**:
  - "Analiza Wg Spółek" - wykres + tabela spółek
  - "Analiza Wg Sektorów" - wykres + ranking sektorów
- **Wykresy kołowe** (matplotlib) z automatycznym grupowaniem "Pozostałe"
- **Tabele** (Tkinter Treeview) z sortowaniem wg udziału

## 🔧 Konfiguracja

### Zmiana sektorów (ręczne nadpisanie)
Edytuj `STATIC_SECTORS` w `sectors.py`:

```python
STATIC_SECTORS = {
    "TICKER": "Nazwa Sektoru",
    # ...
}
```

### Zmiana mapowania WIG-* → Sektor
Edytuj `INDEX_TO_SECTOR` w `sectors.py`:

```python
INDEX_TO_SECTOR = {
    "WIG-BANKI": "Finanse",
    "WIG-BUDOW": "Budownictwo",
    # ...
}
```

## 🐛 Rozwiązywanie problemów

### Program nie pobiera danych
- Sprawdź połączenie internetowe
- Upewnij się, że Edge jest zainstalowany
- Usuń `wig_data.db` i uruchom ponownie

### Błędne sektory
- Sprawdź `STATIC_SECTORS` w `sectors.py`
- Usuń `wig_data.db` aby wymusić ponowne pobranie

### Błędne udziały procentowe
- Usuń `wig_data.db`
- Sprawdź, czy GPW Benchmark nie zmienił struktury tabeli

## 📝 Licencja

MIT License - możesz swobodnie używać, modyfikować i dystrybuować ten kod.

## 👨‍💻 Autor

Projekt stworzony do analizy polskiego rynku akcji małych spółek (sWIG80).

## 🔗 Linki

- [GPW Benchmark - sWIG80](https://gpwbenchmark.pl/karta-indeksu?isin=PL9999999060)
- [BiznesRadar](https://www.biznesradar.pl/)
- [GPW - Giełda Papierów Wartościowych](https://www.gpw.pl/)

---

**Wersja:** 1.0  
**Data ostatniej aktualizacji:** 2026-01-28
