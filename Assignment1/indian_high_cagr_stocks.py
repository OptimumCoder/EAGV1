from jugaad_data.nse import stock_df
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np

def get_stock_growth(symbol):
    try:
        # Set date range for last 2 months
        end_date = date.today()
        start_date = end_date - timedelta(days=60)  # Approximately 2 months
        
        print(f"\nFetching data for {symbol}...", end='')
        
        # Fetch historical data using jugaad_data
        hist = stock_df(
            symbol=symbol,
            from_date=start_date,
            to_date=end_date,
            series="EQ"
        )
        
        if hist.empty:
            print("Failed! No data available")
            return None
            
        print("Success!")
        
        if len(hist) < 30:  # Require at least 30 trading days of data
            print(f"Warning: Insufficient data ({len(hist)} days)")
            return None
        
        # Get first and last valid closing prices
        initial_price = hist['CLOSE'].iloc[0]
        final_price = hist['CLOSE'].iloc[-1]
        
        if pd.isna(initial_price) or pd.isna(final_price):
            print(f"Warning: Invalid price data")
            return None
            
        if initial_price <= 0 or final_price <= 0:
            print(f"Warning: Zero or negative price detected")
            return None
        
        # Calculate metrics
        growth_pct = ((final_price - initial_price) / initial_price) * 100
        avg_volume = hist['VOLUME'].mean()
        daily_returns = hist['CLOSE'].pct_change()
        volatility = daily_returns.std() * 100
        
        # Calculate additional metrics
        high_52week = hist['HIGH'].max()
        low_52week = hist['LOW'].min()
        current_price = hist['CLOSE'].iloc[-1]
        distance_from_high = ((high_52week - current_price) / high_52week) * 100
        
        # Calculate moving averages
        ma_20 = hist['CLOSE'].rolling(window=20).mean().iloc[-1]
        ma_50 = hist['CLOSE'].rolling(window=50).mean().iloc[-1]
        
        return {
            'Growth (%)': round(growth_pct, 2),
            'Current Price': round(final_price, 2),
            'Initial Price': round(initial_price, 2),
            'Avg Daily Volume': int(avg_volume),
            'Volatility (%)': round(volatility, 2),
            'Distance from High (%)': round(distance_from_high, 2),
            '52W High': round(high_52week, 2),
            '52W Low': round(low_52week, 2),
            '20D MA': round(ma_20, 2) if not pd.isna(ma_20) else None,
            '50D MA': round(ma_50, 2) if not pd.isna(ma_50) else None
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    # List of major Indian stocks (using correct NSE symbols)
    nifty_symbols = [
        # Large Cap Companies
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", 
        "ITC", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
        "BAJFINANCE", "SBIN", "WIPRO", "HCLTECH", "ADANIENT", "TECHM",
        
        # IT & Technology
        "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM",
        
        # Auto & Manufacturing
        "TATAMOTORS", "MARUTI", "HEROMOTOCO",
        
        # Consumer & Retail
        "HINDUNILVR", "ITC", "TITAN", "ASIANPAINT", "NESTLEIND", "BRITANNIA"
    ]
    
    # Remove duplicates while preserving order
    nifty_symbols = list(dict.fromkeys(nifty_symbols))
    
    results = []
    total_stocks = len(nifty_symbols)
    
    current_date = datetime.now()
    start_date = (current_date - timedelta(days=60)).strftime('%d %B %Y')
    end_date = current_date.strftime('%d %B %Y')
    
    print(f"Analyzing {total_stocks} major Indian stocks from {start_date} to {end_date}...")
    print("(Note: This analysis focuses on the most actively traded stocks)")
    
    for i, symbol in enumerate(nifty_symbols, 1):
        data = get_stock_growth(symbol)
        if data is not None:
            results.append({'Symbol': symbol, **data})
            
    if results:
        df = pd.DataFrame(results)
        
        # Sort by growth percentage
        df = df.sort_values('Growth (%)', ascending=False)
        
        # Show all stocks and their performance
        print("\nAll Analyzed Stocks Performance:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df.to_string(index=False))
        
        # Filter and display high growth stocks
        high_growth = df[df['Growth (%)'] >= 25]
        
        if not high_growth.empty:
            print("\nHigh Growth Stocks (≥25% in last 2 months):")
            print(high_growth.to_string(index=False))
            
            # Additional statistics
            print(f"\nSummary Statistics:")
            print(f"Total stocks analyzed: {len(df)}")
            print(f"Stocks with ≥25% growth: {len(high_growth)}")
            print(f"Average growth of top performers: {high_growth['Growth (%)'].mean():.2f}%")
            print(f"Average volatility of top performers: {high_growth['Volatility (%)'].mean():.2f}%")
            
            # Additional insights
            print("\nTop Performers Analysis:")
            print(f"Average distance from 52-week high: {high_growth['Distance from High (%)'].mean():.2f}%")
            
            print("\nNote: These stocks have shown significant short-term growth.")
            print("Please conduct thorough research before making any investment decisions.")
        else:
            print("\nNo stocks found with ≥25% growth in the last 2 months.")
    else:
        print("\nNo valid stock data found for analysis.")

if __name__ == "__main__":
    main() 