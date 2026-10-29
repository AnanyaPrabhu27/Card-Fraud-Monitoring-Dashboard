# Card Fraud Monitoring Dashboard

An interactive dashboard for exploring credit card fraud across 100,000 transactions from 2026. Filter the data, explore where and when fraud happens, and export the flagged cases.

**Live demo:** [add your Streamlit link here](https://share.streamlit.io)

![Dashboard screenshot](screenshot.png)

## Features

- **KPI cards** for transactions, total volume, fraud rate and fraud losses, all updating with the filters
- **Sidebar filters** for date range, channel, merchant category and transaction amount
- **Five tabs:**
  - **Trends:** fraud rate and losses by month
  - **Where it happens:** fraud rate by channel, merchant country and category
  - **Fraud types:** cases and losses per type, with average loss per case
  - **Patterns:** fraud by hour of day, fraud vs. legitimate amounts, and risk signals such as international, chip and weekend transactions
  - **Flagged transactions:** a sortable table of fraud cases with CSV export
- **Hover tooltips** on every chart
- **Dark theme** with a custom layout

## What the data shows

- Fraud spikes at night, from about 2% in the daytime to **11% at 3 AM**
- **Online** transactions see about 4x the fraud rate of in-store ones (3.2% vs 0.8%)
- **Online Retail** and **Travel & Airlines** are the riskiest merchant categories, at around 3%
- **Card-not-present** fraud is the most common type
- Overall, **2.06%** of transactions are fraudulent, with about **$280K** lost out of $12.7M in volume

## Project structure

```
├── app.py                 # the dashboard
├── fraud.csv.gz           # dataset (compressed, ~7 MB)
├── requirements.txt
├── screenshot.png
└── .streamlit/
    └── config.toml        # dark theme settings
```

## Data

[Credit Card Fraud Detection Dataset 2026](https://www.kaggle.com/datasets/mohankrishnathalla/credit-card-fraud-detection-dataset-2026) from Kaggle: 100,000 transactions with 43 features. The full dataset is included as `fraud.csv.gz`, and pandas reads it directly with no unzipping needed.

## Built with

Python · pandas · Streamlit · Plotly

## Author

**Ananya Prabhu**
