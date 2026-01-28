# WIG Scalper - System Handlowy v2.0 🚀

Profesjonalna platforma analityczna dla indeksu **sWIG80** (small caps) oraz szerokiego rynku GPW. Aplikacja łączy w sobie automatyczne pobieranie danych, zaawansowaną wizualizację (Heatmapa, Wykresy) oraz nowoczesny interfejs w trybie Dark Mode.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-active.svg)

## 🌟 Nowości w wersji 2.0

- **Nowoczesny UI (Dark Theme)**: Spójny, profesjonalny ciemny motyw (`#2b2b2b`).
- **3 Dedykowane Zakładki**:
    1.  **Skład Indeksu**: Tabela wszystkich spółek + Wykres "Top 10" (kolorowany sektorowo).
    2.  **Sektory**: Struktura całego indeksu + Tabela spółek posortowana sektorami.
    3.  **Heatmapa**: Pełnoekranowa mapa rynku (Treemap) z aktualizacją cen na żywo.
- **Inteligentne Kolory**: 
    - Paleta `tab20` (żywe kolory).
    - Spójność: Spółka na wykresie "Top 10" ma ten sam kolor co jej sektor na wykresie ogólnym.
    - Unikalność: Każda spółka w Top 10 wyróżnia się własnym odcieniem.
- **Wydajność**: Wielowątkowe pobieranie danych (threading) - GUI nie zamarza podczas odświeżania cen.

## 🛠️ Funkcje Główne

- **Automatyzacja**: Samodzielne pobieranie cen (`yfinance`) i struktury portfela.
- **Baza Danych**: SQLite z automatycznym backupem i cache'owaniem.
- **Sortowanie i Filtrowanie**: Błyskawiczny podgląd największych i najmniejszych spółek.
- **Heatmapa Rynku**: Wizualizacja "zielono/czerwono" pokazująca nastroje na rynku w czasie rzeczywistym.

## 📸 Interfejs

### 1. Skład Indeksu
*Pełna lista spółek połączona z wykresem liderów.*

### 2. Sektory
*Analiza strukturalna - które branże rządzą rynkiem (Banki, Budownictwo, Gaming).*

### 3. Heatmapa
*Szybki rzut oka na cały rynek - wielkość kafelka to udział w indeksie, kolor to zmiana ceny.*

## 🚀 Instalacja i Uruchomienie

### Wymagania
- Python 3.10+
- Internet (do pobierania notowań)

### Instalacja
```bash
pip install -r requirements.txt
```

### Uruchomienie
Wystarczy dwukrotnie kliknąć plik:
`run_app.bat`

Lub z konsoli:
```bash
python main.py
```

## 🏗️ Struktura Projektu (Clean Architecture)

```
wig/
├── main.py                 # Punkt startowy (GUI + Wątki)
├── dashboard.py            # Logika interfejsu (Wykresy + Tabele)
├── market_data.py          # Pobieranie danych (YFinance + Mapowania)
├── visualizer.py           # Moduł Heatmapy
├── database.py             # Obsługa bazy danych SQLite
├── sectors.py              # Logika klasyfikacji sektorowej
├── wig_data.db             # Baza danych (auto-generowana)
└── run_app.bat             # Skrypt startowy
```

## 👨‍💻 Autor
Projekt rozwijany przez **Wneq1**. 
Skupiony na analizie technicznej i fundamentalnej polskich spółek giełdowych.

---
**Wersja:** 2.0 (Premium)
**Data ostatniej aktualizacji:** 2026-01-28
