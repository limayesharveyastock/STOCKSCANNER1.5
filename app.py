# ✅ Define Nifty 50 universe explicitly
NIFTY50_STOCKS = [
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL",
    "BHARTIARTL","BPCL","BRITANNIA","CIPLA","COALINDIA","DRREDDY","EICHERMOT","GRASIM","HCLTECH","HDFCBANK",
    "HDFCLIFE","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","INDIGO","ITC","JSWSTEEL","JIOFIN",
    "KOTAKBANK","LT","M&M","MARUTI","MAXHEALTH","NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE",
    "SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM","TITAN","TRENT",
    "ULTRACEMCO","UPL","WIPRO"
]

# --- Indicator calculation ---
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # VWMA & RSI
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Volume averages
    df['VOL_MA_20'] = ta.sma(df['volume'], length=20)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    
    # Supertrend
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

# --- Buy/Sell crossover logic ---
def get_crossover_signal(df):
    if len(df) < 3:
        return "No Cross"
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev_2 = df.iloc[-3]
    
    # Fresh cross
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']:
        return "🔥 BUY SIGNAL (9 crosses 26 up)"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']:
        return "❄️ SELL SIGNAL (9 crosses 26 down)"
        
    # One bar ago
    if prev_2['VWMA_9'] <= prev_2['VWMA_26'] and prev['VWMA_9'] > prev['VWMA_26']:
        return "🔥 BUY (1 bar ago)"
    elif prev_2['VWMA_9'] >= prev_2['VWMA_26'] and prev['VWMA_9'] < prev['VWMA_26']:
        return "❄️ SELL (1 bar ago)"
        
    return "No Cross"

# --- Trend evaluation ---
def evaluate_trend(latest, last_cross_price, tf="15M"):
    curr_price = float(latest['close'])
    vol_ma = float(latest['VOL_MA_50']) if tf == "1D" else float(latest['VOL_MA_20'])
    curr_vol = float(latest['volume'])
    rsi = float(latest['RSI'])
    
    if curr_vol > vol_ma and rsi > 60 and curr_price > last_cross_price:
        return "🟢 BULLISH"
    elif curr_vol > vol_ma and rsi < 40 and curr_price < last_cross_price:
        return "🔴 BEARISH"
    else:
        return "⚪ NEUTRAL"

# --- Scanner loop ---
def execute_parallel_scan(kite, token_lookup):
    results = []
    def worker(symbol):
        token = token_lookup.get(symbol)
        if not token:
            return None
        try:
            hist_15m = kite.historical_data(
                token,
                from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'),
                interval="15minute"
            )
            if not hist_15m or len(hist_15m) < 110:
                return None
            df_15m = pd.DataFrame(hist_15m)
            df_15m = calculate_indicators(df_15m)
            latest_15m = df_15m.iloc[-1]
            
            vwma_cross_signal = get_crossover_signal(df_15m)
            above = df_15m['VWMA_9'] > df_15m['VWMA_26']
            cross_mask = above != above.shift()
            cross_mask.iloc[0] = False
            cross_df = df_15m[cross_mask]
            last_cross_price = float(cross_df['close'].iloc[-1]) if not cross_df.empty else float(latest_15m['close'])
            
            trend = evaluate_trend(latest_15m, last_cross_price, tf="15M")
            
            return {
                "Stock": symbol,
                "LTP": round(latest_15m['close'], 2),
                "RSI": round(latest_15m['RSI'], 2),
                "VWMA Cross": vwma_cross_signal,
                "Last Cross Price": round(last_cross_price, 2),
                "Trend": trend
            }
        except Exception:
            return None
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, symbol) for symbol in NIFTY50_STOCKS]
        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)
    return pd.DataFrame(results)
