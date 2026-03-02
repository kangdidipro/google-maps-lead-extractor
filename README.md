# 🚀 G-LANCE: Google Maps Lead Extractor

![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Playwright](https://img.shields.io/badge/framework-Playwright-orange.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**G-LANCE** is a high-performance automation tool designed for B2B lead generation. It bypasses manual searching by deep-scraping business details directly from Google Maps and exporting them into organized Excel reports.

## ✨ Key Features
- **Deep Data Mining:** Extracts Name, Address, Phone, Website, and Google Maps URL.
- **Dynamic Search:** Input any keyword via CLI.
- **Anti-Detection:** Built-in human behavior simulation with random delays.
- **Professional Reports:** Automatic export to `.xlsx` format.

## 🛠️ Tech Stack
- **Engine:** Python 3.13
- **Automation:** Playwright (Chromium)
- **Data Handling:** Pandas & OpenPyXL

## 🚀 How to Run

1. **Clone & Install:**
   ```bash
   git clone [https://github.com/kangdidipro/google-maps-lead-extractor.git](https://github.com/kangdidipro/google-maps-lead-extractor.git)
   cd google-maps-lead-extractor
   python -m venv venv
   source venv/Scripts/activate  # For Windows
   pip install -r requirements.txt
   playwright install chromium