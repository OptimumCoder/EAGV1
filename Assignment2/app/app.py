from flask import Flask, jsonify
from flask_cors import CORS
from jugaad_data.nse import bhavcopy_save
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
import os
import tempfile
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="AIzaSyAQSIEsB2zL5Ez0IPHMU9vCNHRStc8LvlA")
model = genai.GenerativeModel('gemini-2.0-flash')

app = Flask(__name__)
# Configure CORS to allow all origins
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

def is_weekday(d):
    # Return True if the date is a weekday (Monday = 0, Sunday = 6)
    return d.weekday() < 5

def bhavcopy_save_with_retry(date, directory, max_retries=3):
    """Try to download bhavcopy with retries"""
    for attempt in range(max_retries):
        try:
            bhavcopy_save(date, directory)
            csv_file = os.path.join(directory, f"cm{date.strftime('%d%b%Y').upper()}bhav.csv")
            if os.path.exists(csv_file):
                return True
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Failed to download data for {date} after {max_retries} attempts: {str(e)}")
            else:
                print(f"Attempt {attempt + 1} failed for {date}, retrying...")
    return False

def analyze_stock_with_ai(stock_data):
    """Use Gemini to analyze stock performance"""
    if 'Error' in stock_data:
        return None
        
    prompt = f"""Brief analysis of {stock_data['Symbol']}:
Price: ₹{stock_data['Current Price']}, Change: {stock_data['Price Change (%)']}%
Volume: {stock_data['Volume']}, Value: ₹{stock_data['Value']}
Period: {stock_data['Date_Range']}
Provide one concise sentence about price trend and trading activity."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Analysis error for {stock_data['Symbol']}: {str(e)}")
        return None

def get_stock_growth(symbol):
    try:
        # Use a 2-week date range
        end_date = date(2024, 3, 20)  # Most recent date
        start_date = end_date - timedelta(days=14)  # 2 weeks before
        
        print(f"Fetching data for {symbol} from {start_date} to {end_date}")
        
        # Create a temporary directory to store the bhavcopy files
        with tempfile.TemporaryDirectory() as temp_dir:
            all_data = []
            current_date = start_date
            
            # Fetch data for each day in the range
            while current_date <= end_date:
                try:
                    # Skip weekends
                    if not is_weekday(current_date):
                        print(f"Skipping weekend date: {current_date}")
                        current_date += timedelta(days=1)
                        continue
                        
                    print(f"Fetching bhavcopy for date {current_date}")
                    if bhavcopy_save_with_retry(current_date, temp_dir):
                        csv_file = os.path.join(temp_dir, f"cm{current_date.strftime('%d%b%Y').upper()}bhav.csv")
                        
                        if os.path.exists(csv_file):
                            df = pd.read_csv(csv_file)
                            stock_data = df[df['SYMBOL'] == symbol].iloc[0] if not df[df['SYMBOL'] == symbol].empty else None
                            
                            if stock_data is not None:
                                all_data.append({
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'close': float(stock_data['CLOSE']),
                                    'open': float(stock_data['OPEN']),
                                    'high': float(stock_data['HIGH']),
                                    'low': float(stock_data['LOW']),
                                    'volume': int(stock_data['TOTTRDQTY']),
                                    'value': float(stock_data['TOTTRDVAL'])
                                })
                            else:
                                print(f"No data found for {symbol} on {current_date}")
                    else:
                        print(f"Skipping date {current_date} due to download failure")
                    
                except Exception as e:
                    print(f"Error processing {symbol} for date {current_date}: {str(e)}")
                
                current_date += timedelta(days=1)
            
            if not all_data:
                return {
                    'Symbol': symbol,
                    'Error': f'No data available between {start_date} and {end_date}',
                    'Date_Range': f'{start_date} to {end_date}'
                }
            
            # Calculate aggregated metrics
            latest_data = all_data[-1]
            avg_volume = sum(d['volume'] for d in all_data) / len(all_data)
            total_value = sum(d['value'] for d in all_data)
            price_change = ((latest_data['close'] - all_data[0]['close']) / all_data[0]['close']) * 100
            
            result = {
                'Symbol': symbol,
                'Current Price': latest_data['close'],
                'Open': latest_data['open'],
                'High': max(d['high'] for d in all_data),
                'Low': min(d['low'] for d in all_data),
                'Volume': int(avg_volume),
                'Value': total_value,
                'Price Change (%)': round(price_change, 2),
                'Date_Range': f'{start_date} to {end_date} (Trading Days: {len(all_data)})',
                'Days_With_Data': len(all_data)
            }
            
            # Add AI analysis
            ai_analysis = analyze_stock_with_ai(result)
            if ai_analysis:
                result['AI_Analysis'] = ai_analysis
                
            return result
                
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return {
            'Symbol': symbol,
            'Error': str(e),
            'Date_Range': f'{start_date} to {end_date}'
        }

@app.route('/api/stocks')
def get_stocks():
    nifty_symbols = [
        # Top 10 Major Companies with reliable data
        "RELIANCE",    # Reliance Industries
        "TCS",        # Tata Consultancy Services
        "HDFCBANK",   # HDFC Bank
        "BHARTIARTL", # Bharti Airtel
        "SBIN",       # State Bank of India
        "LT",         # Larsen & Toubro
        "ADANIENT",   # Adani Enterprises
        "ASIANPAINT", # Asian Paints
        "TATASTEEL",  # Tata Steel
        "TITAN"       # Titan Company
    ]
    
    results = []
    
    print("Starting stock data collection...")
    for symbol in nifty_symbols:
        try:
            print(f"Processing {symbol}...")
            data = get_stock_growth(symbol)
            if data is not None:
                results.append(data)
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
            continue
    
    # Calculate statistics
    if results:
        total_stocks = len(results)
        valid_stocks = [stock for stock in results if 'Error' not in stock]
        
        if valid_stocks:
            avg_price = sum(stock['Current Price'] for stock in valid_stocks) / len(valid_stocks)
            avg_volume = sum(stock['Volume'] for stock in valid_stocks) / len(valid_stocks)
            total_value = sum(stock['Value'] for stock in valid_stocks)
            avg_price_change = sum(stock['Price Change (%)'] for stock in valid_stocks) / len(valid_stocks)
            
            stats = {
                'total_analyzed': total_stocks,
                'successful_fetches': len(valid_stocks),
                'avg_price': avg_price,
                'avg_volume': avg_volume,
                'total_value': total_value,
                'avg_price_change': avg_price_change,
                'date_range': valid_stocks[0]['Date_Range']
            }
        else:
            stats = {
                'total_analyzed': total_stocks,
                'successful_fetches': 0,
                'avg_price': 0,
                'avg_volume': 0,
                'total_value': 0,
                'avg_price_change': 0,
                'date_range': 'No data available'
            }
    else:
        stats = {
            'total_analyzed': 0,
            'successful_fetches': 0,
            'avg_price': 0,
            'avg_volume': 0,
            'total_value': 0,
            'avg_price_change': 0,
            'date_range': 'No data available'
        }
    
    return jsonify({
        'stocks': results,
        'stats': stats,
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002) 