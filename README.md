# NSE Dashboard

## Overview

NSE Dashboard is a Streamlit-based web application designed to analyze National Stock Exchange (NSE) Bhavcopy data. It automates data collection, processes historical trading information, and provides interactive visualizations and analytics to help users identify market trends, delivery-based opportunities, and unusual trading activity.

The project is built to update automatically with the latest available market data, ensuring that users always have access to current insights.

## Features

* 📈 Interactive dashboard for NSE market analysis
* 📊 Delivery percentage analysis
* 📦 Trading volume analytics
* 📉 Daily, weekly, monthly, and quarterly average volume comparison
* 🔍 Stock filtering and sorting
* ⚡ Volume spike detection
* 📅 Historical data analysis using multiple Bhavcopy files
* 🔄 Automated daily data updates using GitHub Actions

## Technology Stack

* **Language:** Python
* **Framework:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Automation:** GitHub Actions
* **Version Control:** Git & GitHub

## Data Source

The dashboard uses official NSE Bhavcopy data, which includes information such as:

* Stock Symbol
* Open Price
* High Price
* Low Price
* Close Price
* Total Traded Quantity
* Delivery Quantity
* Delivery Percentage

Historical Bhavcopy files are downloaded and processed automatically to generate rolling analytics.

## Analytics Included

The dashboard provides insights such as:

* Highest delivery percentage stocks
* Trading volume rankings
* Daily average volume
* Weekly average volume
* Monthly average volume
* Quarterly (3-Month) average volume
* Volume spike identification
* Historical stock performance trends

## Installation

Clone the repository:

```bash
git clone https://github.com/jayanigupta/nse-dashboard.git
cd nse-dashboard
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

## Automated Data Updates

The project includes GitHub Actions workflows that automatically:

* Download the latest NSE Bhavcopy files
* Update historical datasets
* Recalculate rolling average volume metrics
* Push updated data to the repository

This automation keeps the dashboard synchronized with the latest available market data.

## Project Structure

```text
nse-dashboard/
│
├── app.py
├── data/
│   └── sec_bhavdata_full_*.csv
├── download.py
├── download_history.py
├── process_data.py
├── requirements.txt
├── .github/
│   └── workflows/
└── README.md
```

## Future Improvements

Potential enhancements include:

* Advanced stock screening
* Technical indicator integration
* Custom watchlists
* Portfolio tracking
* Interactive charts and additional visualizations
* Performance optimization for larger historical datasets

## Disclaimer

This project is intended for educational and analytical purposes only. The information provided should not be interpreted as financial or investment advice. Users should conduct their own research before making investment decisions.
