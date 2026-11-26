# 🚀 G-LANCE: Google Maps B2B Lead Extractor

![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
![Playwright](https://img.shields.io/badge/automation-Playwright-orange.svg)
![Data Processing](https://img.shields.io/badge/data-Pandas%20%7C%20OpenPyXL-150458.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**G-LANCE** is an automated data extraction and B2B lead generation pipeline built with Python and Playwright. It streamlines market research and outbound prospecting by crawling dynamic Google Maps search results, parsing detailed business profiles, deduplicating records, and exporting structured datasets directly into business-ready Excel (`.xlsx`) reports.

---

## 📋 Table of Contents
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Output Data Schema & Preview](#-output-data-schema--preview)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Architecture & Engineering Highlights](#-architecture--engineering-highlights)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## ✨ Key Features
- **Deep Business Profiling:** Captures essential B2B contact and location attributes including Business Name, Full Address, Phone Number, Official Website, and direct Google Maps URL.
- **Dynamic CLI Search:** Supports custom niche and geographic keyword queries directly from the command line without modifying source code.
- **Resilient Browser Automation:** Simulates human-like viewport scrolling and randomized interaction delays to reliably load lazy-rendered result cards and reduce rate-limiting friction.
- **Automated Data Normalization:** Uses Pandas and OpenPyXL to clean extracted fields, remove duplicate entries, and generate formatted `.xlsx` spreadsheets ready for CRM import.

---

## 🛠️ Tech Stack
- **Language:** Python 3.13+
- **Browser Automation:** Playwright (Chromium)
- **Data Manipulation & Export:** Pandas, OpenPyXL

---

## 📊 Output Data Schema & Preview

Each run exports an `.xlsx` file containing structured records. Below is an illustrative example of the generated dataset:

| Business Name | Phone Number | Website | Full Address | Google Maps URL |
| :--- | :--- | :--- | :--- | :--- |
| Apex Digital Agency | +1 512-555-0148 | https://apexdigital.example | 402 W 4th St, Austin, TX | `https://www.google.com/maps/place/...` |
| Bluebonnet Roasters | +1 512-555-0192 | https://bluebonnet.example | 1108 E 6th St, Austin, TX | `https://www.google.com/maps/place/...` |
| Lone Star Logistics | +1 512-555-0174 | https://lonestar.example | 2900 S Congress Ave, Austin, TX | `https://www.google.com/maps/place/...` |

---

## 🚀 Getting Started

### Prerequisites
- Python **3.13** or higher installed on your system.
- `pip` package manager.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/kangdidipro/google-maps-lead-extractor.git](https://github.com/kangdidipro/google-maps-lead-extractor.git)
   cd google-maps-lead-extractor
