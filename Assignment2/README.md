# Indian Stock Market Analysis

This application provides real-time analysis of Indian stocks, focusing on growth metrics, technical indicators, and market trends.

## Features

- Fetches real-time stock data for major Indian companies
- Calculates key metrics like growth percentage, volatility, and moving averages
- Provides statistical analysis of high-growth stocks
- RESTful API endpoint for data access

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask server:
```bash
python app/app.py
```

2. The server will start on `http://localhost:5000`

## API Endpoints

### GET /api/stocks

Returns a JSON object containing:
- List of analyzed stocks with their metrics
- Statistical summary of high-growth stocks
- Last update timestamp

## Data Points

For each stock, the following metrics are calculated:
- Growth percentage (60-day period)
- Current and initial prices
- Average daily volume
- Volatility
- Distance from 52-week high
- 20-day and 50-day moving averages

## Note

This application uses the `jugaad-data` library to fetch NSE (National Stock Exchange) data. Please ensure you have a stable internet connection for real-time data retrieval. 