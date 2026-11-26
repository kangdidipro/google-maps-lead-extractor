# 🚀 G-LANCE PRO — Google Maps B2B Lead Extractor

![Python Version](https://img.shields.io/badge/python-3.10--3.13-blue.svg)
![Playwright](https://img.shields.io/badge/automation-Playwright-orange.svg)
![Data Processing](https://img.shields.io/badge/data-Pandas%20%7C%20OpenPyXL-150458.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**G-LANCE PRO** is an automated data extraction and B2B lead generation CLI pipeline built with Python, Playwright, and Pandas. It crawls dynamic Google Maps search results, parses verified business profiles, deduplicates records, and exports structured datasets directly into business-ready Excel (`.xlsx`) spreadsheets for sales prospecting and market research.

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Prerequisites](#5-prerequisites)
6. [Installation on Windows](#6-installation-on-windows)
7. [Virtual Environment Setup](#7-virtual-environment-setup)
8. [Dependency Installation](#8-dependency-installation)
9. [Playwright Chromium Installation](#9-playwright-chromium-installation)
10. [Basic Usage](#10-basic-usage)
11. [CLI Parameters](#11-cli-parameters)
12. [Usage Examples](#12-usage-examples)
13. [Understanding Search Limits](#13-understanding-search-limits)
14. [Excel Output Explanation](#14-excel-output-explanation)
15. [Troubleshooting](#15-troubleshooting)
16. [Disclaimer](#16-disclaimer)
17. [License](#17-license)

---

## 1. Project Overview

Finding qualified local B2B leads manually on Google Maps is repetitive and time-consuming. **G-LANCE PRO** automates this workflow from the command line: it navigates Google Maps search feeds, performs realistic viewport scrolling, extracts contact details for businesses, normalizes missing attributes, removes duplicates, and generates timestamped Excel reports.

---

## 2. Key Features

- **Dynamic CLI Interface:** Command-line controls powered by `argparse` with backward compatibility for unquoted queries.
- **Configurable Limits & Scrolling:** Decoupled controls for maximum lead processing targets (`--limit`) and scroll depth (`--scrolls`).
- **Early Termination & Stagnation Detection:** Intelligently stops scrolling when sufficient leads are found or when Google Maps feed returns no additional cards after consecutive attempts.
- **Headless & Headed Browser Execution:** Toggle visual browser observation or silent background runs via `--headless`.
- **Deep Profile Parsing:** Captures Business Name, Full Address, Phone Number, Website, and Google Maps URL.
- **Robust Exception & Field Handling:** Gracefully falls back to `"N/A"` for missing business contact attributes without crashing.
- **Non-destructive Excel Exports:** Writes timestamped (`YYYYMMDD_HHMMSS`) `.xlsx` spreadsheets to ensure prior runs are never overwritten.

---

## 3. Technology Stack

- **Core Runtime:** Python 3.10–3.13 (Python 3.10 and 3.13 independently verified; Python 3.11 and 3.12 are supported per dependency specifications but were not independently tested on this workstation)
- **Browser Automation:** Playwright (`playwright>=1.48.0,<2.0.0`)
- **Data Engineering:** Pandas (`pandas>=2.2.3,<3.0.0`) & OpenPyXL (`openpyxl==3.1.2`)
- **CLI Parsing:** Python Standard Library `argparse`

---

## 4. Project Structure

```
google-maps-lead-extractor/
│
├── config.py                 # Default configurations (BASE_URL, default HEADLESS, SCROLL_COUNT)
├── main.py                   # CLI entry point, argument parsing, session lifecycle orchestration
├── scraper.py                # Playwright scraping engine, scrolling, and lead card extraction
├── processor.py              # Pandas data cleaning, deduplication, and Excel output handling
├── utils.py                  # Shared URL and text normalization helper functions
├── requirements.txt          # Project Python package dependencies
├── test_regression_rev3.py   # Comprehensive automated test suite (19 regression tests)
├── README.md                 # Project documentation
├── .gitignore                # Git ignore rules
├── update.bat                # Git staging, commit, and push utility script
└── reports/                  # Architecture, audit, and verification reports
    ├── GLANCE-CLI-ENHANCEMENT.md
    ├── GLANCE-REVISION-3-DOM-RELIABILITY.md
    ├── GLANCE-REVISION-3.1-SELECTOR-HARDENING.md
    ├── GLANCE-REVISION-3.1.1-LOCATOR-CORRECTION.md
    ├── GLANCE-REVISION-3.1.2-TEST-HARDENING.md
    ├── GLANCE-REVISION-3.1.3-DOCUMENTATION-CORRECTION.md
    └── GLANCE-FINAL-PROJECT-REVIEW.md
```

---

## 5. Prerequisites

Before installing, ensure your Windows workstation meets the following prerequisites:
- **Operating System:** Windows 10 or Windows 11 (64-bit).
- **Python:** Python 3.10 to 3.13 installed (Python 3.10 and 3.13 verified via clean environment installation; Python 3.11 and 3.12 not independently tested). Ensure **"Add Python to PATH"** was checked during installation.
- **Git:** Git for Windows installed.
- **Internet Connectivity:** Stable connection to query Google Maps and install Playwright browser binaries.

---

## 6. Installation on Windows

Open **Command Prompt (cmd.exe)** or **PowerShell** and run:

```bat
cd C:\my-app

git clone https://github.com/kangdidipro/google-maps-lead-extractor.git

cd google-maps-lead-extractor
```

---

## 7. Virtual Environment Setup

Create an isolated virtual environment to prevent dependency conflicts with global packages:

```bat
python -m venv .venv

.venv\Scripts\activate
```

*(Note: When using PowerShell, ensure script execution is enabled via `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` if activation is blocked).*

---

## 8. Dependency Installation

Upgrade `pip` and install all necessary Python packages:

```bat
python -m pip install --upgrade pip

pip install -r requirements.txt
```

*(Note: The project baseline uses `playwright>=1.48.0,<2.0.0`, `pandas>=2.2.3,<3.0.0`, and `openpyxl==3.1.2`, providing official pre-compiled binary wheels across Python 3.10 through Python 3.13 without requiring a C++ compiler).*

---

## 9. Playwright Chromium Installation

Download and install the dedicated Chromium browser binary used by Playwright:

```bat
playwright install chromium
```

---

## 10. Basic Usage

Run a search using your business category and geographic target wrapped in quotes:

```bat
python main.py "Coffee Shop New York"
```

The script will launch a browser window, navigate Google Maps, scroll through the feed, extract up to 20 leads, and save the results into an Excel file in the project folder.

---

## 11. CLI Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `keyword` | String (positional) | *(Required)* | Business query combining industry and location (e.g., `"Dentist Jakarta"`, `Real Estate London`). Multiple unquoted terms are automatically joined. |
| `--limit` | Integer | `20` | Maximum number of unique business listings to deep-scrape. Must be a positive integer (> 0). |
| `--scrolls` | Integer | `5` | Maximum number of scroll operations performed to discover listing cards in the feed. Must be a positive integer (> 0). |
| `--headless` | Flag (Boolean) | `False` | Run Chromium silently in background headless mode without displaying a graphical browser window. |
| `-h`, `--help` | Flag | — | Display the CLI syntax, options reference, and usage examples. |

---

## 12. Usage Examples

### Standard Search (Default Settings: 20 leads, 5 scrolls, visual browser)
```bat
python main.py "Coffee Shop New York"
```

### Expanding Lead Processing Target
```bat
python main.py "Coffee Shop New York" --limit 50
```

### Deep Search with Increased Scrolling
```bat
python main.py "Restaurant Jakarta" --limit 100 --scrolls 15
```

### High-Volume Extraction with Custom Parameters
```bat
python main.py "Digital Agency Singapore" --limit 100 --scrolls 20
```

### Fast Background Headless Extraction
```bat
python main.py "Real Estate London" --limit 50 --headless
```

### Backward Compatibility (Unquoted multi-word arguments)
```bat
python main.py newyork caffee
```

### Display Help Menu
```bat
python main.py --help
```

---

## 13. Understanding Search Limits

To optimize your extraction runs, keep in mind how Google Maps works and how the CLI parameters interact:

1. **Difference Between `--scrolls`, `--limit`, and Available Results:**
   - **`--scrolls`** dictates how many times the scraper scrolls down the listing container to trigger dynamic lazy loading. Each scroll allows Google Maps to load additional business cards into the DOM.
   - **`--limit`** dictates the maximum number of individual business cards that the scraper will open and extract details from.
   - **Actual Available Results** is the actual count of businesses returned by Google Maps for that query in that geographic boundary.
2. **Limits Do Not Guarantee Equal Records:**
   - Setting `--limit 100` instructs the engine to process *up to* 100 businesses. If a specific keyword or small town only has 14 listings, the scraper will discover and extract all 14, and stop gracefully without forcing 100 items.
3. **Keyword Formulation Best Practices:**
   - Combine a specific **business niche** with a **clear locality/city/district**:
     - ✅ `"Boutique Hotel Florence"`
     - ✅ `"Commercial Roofer Dallas TX"`
     - ✅ `"Coworking Space Bandung"`
   - If search results are sparse, increase `--scrolls` or broaden the geographic scope.

---

## 14. Excel Output Explanation

Extracted data is automatically cleaned and exported to an Excel file using the naming pattern:
```
GLANCE_<Cleaned_Keyword>_<YYYYMMDD_HHMMSS>.xlsx
```

Example filename: `GLANCE_Coffee_Shop_New_York_20261126_134940.xlsx`

### Export Data Schema

| Column Name | Description | Example |
| :--- | :--- | :--- |
| `No` | Clean sequential record numbering | `1` |
| `Name` | Registered business title on Google Maps | `Coffee Project New York` |
| `Address` | Standardized street and city address | `239 E 5th St, New York, NY 10003` |
| `Phone` | Local or international contact telephone number | `+1 212-228-7888` |
| `Website` | Official company website or verified social link | `http://www.coffeeprojectny.com/` |
| `Google Maps URL` | Direct Google Maps location URL | `https://www.google.com/maps/place/...` |

- Missing values (e.g., businesses without a public phone or website) are stored as `"N/A"`.
- Duplicate records representing the same Google Maps business identity are removed.
- Different branches of the same business, even when they share an identical business name, are preserved when their Google Maps URLs identify different locations.
- Records with insufficient identity information (missing both Google Maps URL and Name/Address) follow the existing preservation behavior and are retained with an integrity notice rather than being falsely collapsed together.
- Timestamping to seconds (`%Y%m%d_%H%M%S`) ensures consecutive runs never overwrite prior work.

---

## 15. Troubleshooting

- **Issue: `Playwright Host Not Found` or browser launch fails:**
  - Run `playwright install chromium` inside your active virtual environment.
- **Issue: Missing contact info in output:**
  - Some businesses do not provide a phone number or website on their Google profile. The scraper marks these fields safely as `"N/A"` without interrupting extraction.
- **Issue: "No listings found for the search query":**
  - Check your spelling or broaden the search terms. Google Maps may occasionally prompt for a CAPTCHA or geographic verification if automated queries are run excessively.
- **Issue: Script closes immediately:**
  - Verify your virtual environment is active (`.venv\Scripts\activate`) and all dependencies in `requirements.txt` are installed.

---

## 16. Disclaimer

This software is developed strictly for educational, market research, and local business analysis purposes. Users are solely responsible for ensuring that their data collection and scraping practices comply with Google's Terms of Service and local data privacy regulations (e.g., GDPR, CCPA). Do not bypass security gates or flood services with high-frequency concurrent queries.

---

## 17. License

This project is licensed under the **MIT License**. Feel free to use, modify, and distribute according to the license terms.
