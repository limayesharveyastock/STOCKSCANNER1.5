import yfinance as yf
import pandas as pd
import time

# List of your core stocks (Add your full Nifty 500 list here)
tickers = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"] 

def fetch_live_fundamentals():
    data = []
    print(f"Fetching fundamentals for {len(tickers)} stocks...")
    
    for ticker in tickers:
        # Yahoo Finance requires '.NS' for NSE stocks
        yf_ticker = f"{ticker}.NS"
        stock = yf.Ticker(yf_ticker)
        
        try:
            info = stock.info
            
            # Extract live metrics (using .get() prevents crashes if data is missing)
            pe = info.get('trailingPE', 0.0)
            pb = info.get('priceToBook', 0.0)
            industry = info.get('industry', 'Unknown')
            # Yahoo finance gives promoter holding as a decimal (e.g. 0.50 for 50%)
            promoter = info.get('heldPercentInsiders', 0.0) * 100 
            
            # Note: ROCE and Industry PE aren't perfectly standard in yfinance, 
            # so we grab Return on Equity (ROE) as a proxy if ROCE is unavailable.
            roce = info.get('returnOnEquity', 0.0) * 100 

            data.append({
                "Ticker": ticker,
                "Industry": industry,
                "Promoter_Percent": round(promoter, 2),
                "Stock_PE": round(pe, 2),
                "Industry_PE": 0.0, # Hard to get free live Industry PE
                "PB": round(pb, 2),
                "ROCE": round(roce, 2)
            })
            print(f"✅ Fetched {ticker}")
            
        except Exception as e:
            print(f"❌ Failed to fetch {ticker}: {e}")
            
        time.sleep(0.5) # Prevent Yahoo Finance rate limits
        
    # Save to the CSV that your Streamlit app reads
    df = pd.DataFrame(data)
    df.to_csv("stock_fundamentals.csv", index=False)
    print("\n🎉 Update Complete! Saved to stock_fundamentals.csv")

if __name__ == "__main__":
    fetch_live_fundamentals()
