import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_screener_fundamentals(ticker):
    """
    Scrapes live fundamental ratios directly from Screener.in for a given NSE ticker.
    """
    # Map any common structural ticket anomalies if required
    url = f"https://www.screener.in/company/{ticker}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Could not reach Screener for {ticker} (Status Code: {response.status_code})")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Screener stores top card details inside an un-ordered list id 'top-ratios'
        ratio_li_elements = soup.find('ul', id='top-ratios')
        if not ratio_li_elements:
            return None
            
        metrics = {}
        for li in ratio_li_elements.find_all('li'):
            name_span = li.find('span', class_='name')
            value_span = li.find('span', class_='number')
            
            if name_span and value_span:
                # Clean up names to easily cross-match strings
                metric_name = name_span.text.strip().replace('\n', '').replace('  ', '')
                metric_value = value_span.text.strip().replace(',', '')
                metrics[metric_name] = metric_value

        # --- Helper Function to Clean and Convert Strings safely to Float ---
        def clean_val(val_str):
            try:
                return float(val_str) if val_str else 0.0
            except ValueError:
                return 0.0

        # Parse data safely into the exact naming conventions mapped inside your load_metadata loop
        parsed_data = {
            "Ticker": ticker,
            "Stock_PE": clean_val(metrics.get("Stock P/E")),
            "PB": clean_val(metrics.get("Price to Book Value")),
            "ROCE": clean_val(metrics.get("ROCE")),
            "Net Profit Margin (%) FY": clean_val(metrics.get("Net Profit Margin")), # Will match structural search keys
            "Op Profit Growth 3Y Avg (%)": clean_val(metrics.get("Profit growth 3Years")),
            "Sales Growth 3Y Avg (%)": clean_val(metrics.get("Sales growth 3Years")),
            "ROE 3Y Avg (%)": clean_val(metrics.get("Return on Equity")),
            "ROCE 3Y Avg (%)": clean_val(metrics.get("ROCE 3Years")),
            "Avg CFO 3Y (₹ Cr)": clean_val(metrics.get("Average Cash Flow 3Years"))
        }
        return parsed_data

    except Exception as e:
        print(f"❌ Error scraping {ticker}: {e}")
        return None

def update_local_fundamentals_csv(ticker_list):
    """
    Loops through your target layout list, extracts metrics, and compiles a clean local CSV.
    """
    compiled_records = []
    print(f"🚀 Initializing Screener.in extraction for {len(ticker_list)} securities...")
    
    for ticker in ticker_list:
        data = fetch_screener_fundamentals(ticker)
        if data:
            compiled_records.append(data)
            print(f"✅ Extracted data structure for: {ticker}")
        else:
            print(f"⚠️ Skipping or failed record for: {ticker}")
            
        # Crucial pacing buffer to protect your local IP from getting blocked by Screener's firewall
        time.sleep(2.0) 
        
    df = pd.DataFrame(compiled_records)
    df.to_csv("stock_fundamentals.csv", index=False)
    print("\n🎉 Update Complete! Locally stored inside stock_fundamentals.csv")

if __name__ == "__main__":
    # Test sample block matching keys in your app.py
    sample_universe = ["RELIANCE", "TCS", "HDFCBANK", "INFY"]
    update_local_fundamentals_csv(sample_universe)
