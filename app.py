import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 200 Multi-Dimensional Scanner")

# Initialize Kite connection
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

# Dynamically fetch and map all active NSE instrument tokens
@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

# Expanded Nifty 200 Metadata Matrix
STOCK_METADATA = {
    # --- NIFTY 50 CORE ---
    "ADANIENT": {"Industry": "Conglomerate", "Promoter%": 72.6, "PE": 92.4, "Ind_PE": 61.2, "PB": 9.2, "ROCE": 9.8, "52W_H": 3450.0, "52W_L": 2150.0, "5Y_H": 4190.0, "5Y_L": 130.0},
    "ADANIPORTS": {"Industry": "Infrastructure", "Promoter%": 65.9, "PE": 35.1, "Ind_PE": 28.4, "PB": 4.8, "ROCE": 13.2, "52W_H": 1620.0, "52W_L": 990.0, "5Y_H": 1620.0, "5Y_L": 240.0},
    "APOLLOHOSP": {"Industry": "Healthcare", "Promoter%": 29.3, "PE": 88.7, "Ind_PE": 45.6, "PB": 9.4, "ROCE": 11.7, "52W_H": 7400.0, "52W_L": 5700.0, "5Y_H": 7400.0, "5Y_L": 1200.0},
    "ASIANPAINT": {"Industry": "Consumer Goods", "Promoter%": 52.6, "PE": 54.3, "Ind_PE": 51.1, "PB": 15.1, "ROCE": 29.4, "52W_H": 3400.0, "52W_L": 2680.0, "5Y_H": 3590.0, "5Y_L": 1400.0},
    "AXISBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 12.8, "Ind_PE": 15.2, "PB": 1.9, "ROCE": 10.2, "52W_H": 1340.0, "52W_L": 1020.0, "5Y_H": 1340.0, "5Y_L": 330.0},
    "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter%": 55.1, "PE": 32.4, "Ind_PE": 26.8, "PB": 9.8, "ROCE": 31.6, "52W_H": 10700.0, "52W_L": 6200.0, "5Y_H": 10700.0, "5Y_L": 2000.0},
    "BAJFINANCE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 28.9, "Ind_PE": 24.5, "PB": 4.4, "ROCE": 11.8, "52W_H": 7900.0, "52W_L": 6200.0, "5Y_H": 8190.0, "5Y_L": 1900.0},
    "BAJAJFINSV": {"Industry": "Banking & Finance", "Promoter%": 60.7, "PE": 31.2, "Ind_PE": 24.5, "PB": 3.9, "ROCE": 11.5, "52W_H": 1750.0, "52W_L": 1420.0, "5Y_H": 1930.0, "5Y_L": 460.0},
    "BEL": {"Industry": "Defense & Capital Goods", "Promoter%": 51.1, "PE": 48.5, "Ind_PE": 42.1, "PB": 11.2, "ROCE": 26.3, "52W_H": 340.0, "52W_L": 125.0, "5Y_H": 340.0, "5Y_L": 20.0},
    "BHARTIARTL": {"Industry": "Telecom", "Promoter%": 53.8, "PE": 61.2, "Ind_PE": 45.0, "PB": 6.4, "ROCE": 12.4, "52W_H": 1700.0, "52W_L": 980.0, "5Y_H": 1700.0, "5Y_L": 360.0},
    "BPCL": {"Industry": "Energy & Oil", "Promoter%": 53.0, "PE": 14.2, "Ind_PE": 12.1, "PB": 2.1, "ROCE": 17.1, "52W_H": 370.0, "52W_L": 200.0, "5Y_H": 370.0, "5Y_L": 150.0},
    "BRITANNIA": {"Industry": "FMCG", "Promoter%": 50.5, "PE": 52.1, "Ind_PE": 44.3, "PB": 28.4, "ROCE": 49.2, "52W_H": 6400.0, "52W_L": 4700.0, "5Y_H": 6400.0, "5Y_L": 2400.0},
    "CIPLA": {"Industry": "Pharmaceuticals", "Promoter%": 33.5, "PE": 24.6, "Ind_PE": 31.8, "PB": 3.8, "ROCE": 18.3, "52W_H": 1700.0, "52W_L": 1150.0, "5Y_H": 1700.0, "5Y_L": 400.0},
    "COALINDIA": {"Industry": "Energy & Oil", "Promoter%": 63.1, "PE": 9.8, "Ind_PE": 12.1, "PB": 3.4, "ROCE": 52.1, "52W_H": 540.0, "52W_L": 310.0, "5Y_H": 540.0, "5Y_L": 110.0},
    "DRREDDY": {"Industry": "Pharmaceuticals", "Promoter%": 26.7, "PE": 18.9, "Ind_PE": 31.8, "PB": 3.1, "ROCE": 20.4, "52W_H": 1400.0, "52W_L": 960.0, "5Y_H": 1400.0, "5Y_L": 450.0},
    "EICHERMOT": {"Industry": "Automobile", "Promoter%": 49.2, "PE": 29.7, "Ind_PE": 26.8, "PB": 7.2, "ROCE": 27.5, "52W_H": 5100.0, "52W_L": 3500.0, "5Y_H": 5100.0, "5Y_L": 1300.0},
    "GRASIM": {"Industry": "Materials & Cement", "Promoter%": 42.8, "PE": 42.1, "Ind_PE": 30.2, "PB": 2.2, "ROCE": 8.4, "52W_H": 2850.0, "52W_L": 2000.0, "5Y_H": 2850.0, "5Y_L": 450.0},
    "HCLTECH": {"Industry": "Information Technology", "Promoter%": 64.3, "PE": 26.4, "Ind_PE": 28.1, "PB": 6.1, "ROCE": 28.7, "52W_H": 1850.0, "52W_L": 1300.0, "5Y_H": 1850.0, "5Y_L": 410.0},
    "HDFCBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 10.8, "52W_H": 1790.0, "52W_L": 1360.0, "5Y_H": 1790.0, "5Y_L": 750.0},
    "HDFCLIFE": {"Industry": "Banking & Finance", "Promoter%": 50.4, "PE": 78.4, "Ind_PE": 24.5, "PB": 7.8, "ROCE": 9.4, "52W_H": 740.0, "52W_L": 550.0, "5Y_H": 770.0, "5Y_L": 350.0},
    "HEROMOTOCO": {"Industry": "Automobile", "Promoter%": 34.8, "PE": 23.1, "Ind_PE": 26.8, "PB": 4.9, "ROCE": 25.1, "52W_H": 6100.0, "52W_L": 3900.0, "5Y_H": 6100.0, "5Y_L": 1600.0},
    "HINDALCO": {"Industry": "Metals & Mining", "Promoter%": 34.6, "PE": 15.4, "Ind_PE": 18.9, "PB": 1.7, "ROCE": 11.6, "52W_H": 710.0, "52W_L": 460.0, "5Y_H": 710.0, "5Y_L": 90.0},
    "HINDUNILVR": {"Industry": "FMCG", "Promoter%": 61.9, "PE": 58.2, "Ind_PE": 44.3, "PB": 11.4, "ROCE": 27.3, "52W_H": 2770.0, "52W_L": 2200.0, "5Y_H": 2950.0, "5Y_L": 1750.0},
    "ICICIBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 17.5, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 11.3, "52W_H": 1360.0, "52W_L": 980.0, "5Y_H": 1360.0, "5Y_L": 280.0},
    "INDUSINDBK": {"Industry": "Banking & Finance", "Promoter%": 15.9, "PE": 13.1, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 9.9, "52W_H": 1690.0, "52W_L": 1310.0, "5Y_H": 1690.0, "5Y_L": 300.0},
    "INFY": {"Industry": "Information Technology", "Promoter%": 14.8, "PE": 24.1, "Ind_PE": 28.1, "PB": 7.4, "ROCE": 37.2, "52W_H": 1950.0, "52W_L": 1380.0, "5Y_H": 1950.0, "5Y_L": 510.0},
    "ITC": {"Industry": "FMCG", "Promoter%": 0.0, "PE": 26.8, "Ind_PE": 44.3, "PB": 7.2, "ROCE": 39.1, "52W_H": 520.0, "52W_L": 399.0, "5Y_H": 520.0, "5Y_L": 140.0},
    "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter%": 44.8, "PE": 28.2, "Ind_PE": 18.9, "PB": 2.8, "ROCE": 12.1, "52W_H": 1040.0, "52W_L": 760.0, "5Y_H": 1040.0, "5Y_L": 130.0},
    "KOTAKBANK": {"Industry": "Banking & Finance", "Promoter%": 25.9, "PE": 19.1, "Ind_PE": 15.2, "PB": 2.9, "ROCE": 11.1, "52W_H": 1910.0, "52W_L": 1550.0, "5Y_H": 2250.0, "5Y_L": 1000.0},
    "LT": {"Industry": "Defense & Capital Goods", "Promoter%": 0.0, "PE": 37.4, "Ind_PE": 42.1, "PB": 4.9, "ROCE": 14.8, "52W_H": 3900.0, "52W_L": 3100.0, "5Y_H": 3900.0, "5Y_L": 700.0},
    "LTIM": {"Industry": "Information Technology", "Promoter%": 68.6, "PE": 33.7, "Ind_PE": 28.1, "PB": 7.8, "ROCE": 28.4, "52W_H": 6400.0, "52W_L": 4600.0, "5Y_H": 7500.0, "5Y_L": 1100.0},
    "M&M": {"Industry": "Automobile", "Promoter%": 19.3, "PE": 30.2, "Ind_PE": 26.8, "PB": 5.1, "ROCE": 18.2, "52W_H": 3150.0, "52W_L": 1500.0, "5Y_H": 3150.0, "5Y_L": 270.0},
    "MARUTI": {"Industry": "Automobile", "Promoter%": 58.2, "PE": 27.4, "Ind_PE": 26.8, "PB": 4.6, "ROCE": 21.3, "52W_H": 13400.0, "52W_L": 9700.0, "5Y_H": 13400.0, "5Y_L": 4000.0},
    "MAXHEALTH": {"Industry": "Healthcare", "Promoter%": 23.8, "PE": 91.3, "Ind_PE": 45.6, "PB": 8.7, "ROCE": 13.1, "52W_H": 1050.0, "52W_L": 660.0, "5Y_H": 1050.0, "5Y_L": 100.0},
    "NESTLEIND": {"Industry": "FMCG", "Promoter%": 62.8, "PE": 76.4, "Ind_PE": 44.3, "PB": 24.1, "ROCE": 56.4, "52W_H": 2750.0, "52W_L": 2150.0, "5Y_H": 2750.0, "5Y_L": 1200.0},
    "NTPC": {"Industry": "Energy & Oil", "Promoter%": 51.1, "PE": 18.9, "Ind_PE": 12.1, "PB": 2.4, "ROCE": 11.8, "52W_H": 430.0, "52W_L": 290.0, "5Y_H": 430.0, "5Y_L": 70.0},
    "ONGC": {"Industry": "Energy & Oil", "Promoter%": 58.9, "PE": 8.4, "Ind_PE": 12.1, "PB": 1.1, "ROCE": 14.3, "52W_H": 340.0, "52W_L": 190.0, "5Y_H": 340.0, "5Y_L": 60.0},
    "POWERGRID": {"Industry": "Energy & Oil", "Promoter%": 51.3, "PE": 16.2, "Ind_PE": 12.1, "PB": 3.1, "ROCE": 12.9, "52W_H": 365.0, "52W_L": 240.0, "5Y_H": 365.0, "5Y_L": 80.0},
    "RELIANCE": {"Industry": "Energy & Oil", "Promoter%": 50.4, "PE": 26.5, "Ind_PE": 12.1, "PB": 2.3, "ROCE": 10.1, "52W_H": 3200.0, "52W_L": 2200.0, "5Y_H": 3200.0, "5Y_L": 850.0},
    "SBILIFE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 82.1, "Ind_PE": 24.5, "PB": 11.1, "ROCE": 12.1, "52W_H": 1900.0, "52W_L": 1380.0, "5Y_H": 1900.0, "5Y_L": 650.0},
    "SBIN": {"Industry": "Banking & Finance", "Promoter%": 57.5, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 10.5, "52W_H": 915.0, "52W_L": 620.0, "5Y_H": 915.0, "5Y_L": 150.0},
    "SUNPHARMA": {"Industry": "Pharmaceuticals", "Promoter%": 54.5, "PE": 36.8, "Ind_PE": 31.8, "PB": 4.9, "ROCE": 16.4, "52W_H": 1900.0, "52W_L": 1250.0, "5Y_H": 1900.0, "5Y_L": 330.0},
    "TATACONSUM": {"Industry": "FMCG", "Promoter%": 33.6, "PE": 68.2, "Ind_PE": 44.3, "PB": 4.2, "ROCE": 9.1, "52W_H": 1250.0, "52W_L": 900.0, "5Y_H": 1250.0, "5Y_L": 280.0},
    "TATAMOTORS": {"Industry": "Automobile", "Promoter%": 46.4, "PE": 11.6, "Ind_PE": 26.8, "PB": 3.8, "ROCE": 19.4, "52W_H": 1180.0, "52W_L": 650.0, "5Y_H": 1180.0, "5Y_L": 60.0},
    "TATASTEEL": {"Industry": "Metals & Mining", "Promoter%": 33.2, "PE": 45.3, "Ind_PE": 18.9, "PB": 1.9, "ROCE": 9.2, "52W_H": 185.0, "52W_L": 110.0, "5Y_H": 185.0, "5Y_L": 25.0},
    "TCS": {"Industry": "Information Technology", "Promoter%": 71.8, "PE": 30.1, "Ind_PE": 28.1, "PB": 13.2, "ROCE": 51.4, "52W_H": 4600.0, "52W_L": 3600.0, "5Y_H": 4600.0, "5Y_L": 1600.0},
    "TECHM": {"Industry": "Information Technology", "Promoter%": 34.6, "PE": 44.2, "Ind_PE": 28.1, "PB": 4.1, "ROCE": 17.2, "52W_H": 1550.0, "52W_L": 1100.0, "5Y_H": 1800.0, "5Y_L": 480.0},
    "TITAN": {"Industry": "Consumer Goods", "Promoter%": 52.9, "PE": 85.4, "Ind_PE": 51.1, "PB": 19.8, "ROCE": 23.5, "52W_H": 3890.0, "52W_L": 3050.0, "5Y_H": 3890.0, "5Y_L": 800.0},
    "ULTRACEMCO": {"Industry": "Materials & Cement", "Promoter%": 59.9, "PE": 41.2, "Ind_PE": 30.2, "PB": 4.8, "ROCE": 12.8, "52W_H": 12100.0, "52W_L": 8200.0, "5Y_H": 12100.0, "5Y_L": 3000.0},
    "WIPRO": {"Industry": "Information Technology", "Promoter%": 72.8, "PE": 22.9, "Ind_PE": 28.1, "PB": 4.6, "ROCE": 21.1, "52W_H": 550.0, "52W_L": 380.0, "5Y_H": 740.0, "5Y_L": 160.0},
    "JIOFIN": {"Industry": "Banking & Finance", "Promoter%": 47.7, "PE": 122.4, "Ind_PE": 24.5, "PB": 1.8, "ROCE": 4.9, "52W_H": 400.0, "52W_L": 200.0, "5Y_H": 400.0, "5Y_L": 200.0},

    # --- NIFTY JUNIOR / NEXT 50 ADDITIONS ---
    "HAL": {"Industry": "Defense & Capital Goods", "Promoter%": 71.6, "PE": 41.5, "Ind_PE": 42.1, "PB": 10.5, "ROCE": 29.8, "52W_H": 4850.0, "52W_L": 1850.0, "5Y_H": 4850.0, "5Y_L": 280.0},
    "IRFC": {"Industry": "Banking & Finance", "Promoter%": 86.4, "PE": 32.8, "Ind_PE": 15.2, "PB": 4.1, "ROCE": 5.4, "52W_H": 220.0, "52W_L": 32.0, "5Y_H": 220.0, "5Y_L": 20.0},
    "RECLTD": {"Industry": "Banking & Finance", "Promoter%": 52.6, "PE": 11.2, "Ind_PE": 24.5, "PB": 2.2, "ROCE": 9.4, "52W_H": 650.0, "52W_L": 160.0, "5Y_H": 650.0, "5Y_L": 80.0},
    "PFC": {"Industry": "Banking & Finance", "Promoter%": 56.0, "PE": 10.5, "Ind_PE": 24.5, "PB": 1.9, "ROCE": 9.1, "52W_H": 580.0, "52W_L": 150.0, "5Y_H": 580.0, "5Y_L": 75.0},
    "TATAPOWER": {"Industry": "Energy & Oil", "Promoter%": 46.9, "PE": 34.2, "Ind_PE": 12.1, "PB": 3.8, "ROCE": 11.9, "52W_H": 490.0, "52W_L": 210.0, "5Y_H": 490.0, "5Y_L": 30.0},
    "ZOMATO": {"Industry": "FMCG", "Promoter%": 0.0, "PE": 142.1, "Ind_PE": 44.3, "PB": 9.4, "ROCE": 4.2, "52W_H": 280.0, "52W_L": 75.0, "5Y_H": 280.0, "5Y_L": 40.0},
    "VBL": {"Industry": "FMCG", "Promoter%": 63.1, "PE": 88.5, "Ind_PE": 44.3, "PB": 16.2, "ROCE": 28.1, "52W_H": 1650.0, "52W_L": 820.0, "5Y_H": 1650.0, "5Y_L": 120.0},
    "DLF": {"Industry": "Infrastructure", "Promoter%": 74.1, "PE": 72.4, "Ind_PE": 28.4, "PB": 6.2, "ROCE": 7.4, "52W_H": 950.0, "52W_L": 460.0, "5Y_H": 950.0, "5Y_L": 130.0},
    "GAIL": {"Industry": "Energy & Oil", "Promoter%": 51.9, "PE": 14.8, "Ind_PE": 12.1, "PB": 2.2, "ROCE": 15.3, "52W_H": 240.0, "52W_L": 105.0, "5Y_H": 240.0, "5Y_L": 65.0},
    "PNB": {"Industry": "Banking & Finance", "Promoter%": 73.1, "PE": 15.4, "Ind_PE": 15.2, "PB": 1.2, "ROCE": 7.8, "52W_H": 140.0, "52W_L": 50.0, "5Y_H": 140.0, "5Y_L": 25.0},
    "BANKBARODA": {"Industry": "Banking & Finance", "Promoter%": 64.0, "PE": 7.8, "Ind_PE": 15.2, "PB": 1.1, "ROCE": 9.8, "52W_H": 290.0, "52W_L": 160.0, "5Y_H": 290.0, "5Y_L": 40.0},
    "CANBK": {"Industry": "Banking & Finance", "Promoter%": 63.0, "PE": 6.9, "Ind_PE": 15.2, "PB": 1.0, "ROCE": 9.4, "52W_H": 130.0, "52W_L": 60.0, "5Y_H": 130.0, "5Y_L": 15.0},
    "AMBUJACEM": {"Industry": "Materials & Cement", "Promoter%": 67.3, "PE": 44.1, "Ind_PE": 30.2, "PB": 3.9, "ROCE": 11.2, "52W_H": 690.0, "52W_L": 400.0, "5Y_H": 690.0, "5Y_L": 140.0},
    "ACC": {"Industry": "Materials & Cement", "Promoter%": 56.7, "PE": 28.1, "Ind_PE": 30.2, "PB": 2.9, "ROCE": 14.1, "52W_H": 2750.0, "52W_L": 1800.0, "5Y_H": 2750.0, "5Y_L": 900.0},
    "PIDILITIND": {"Industry": "Consumer Goods", "Promoter%": 69.9, "PE": 74.3, "Ind_PE": 51.1, "PB": 18.2, "ROCE": 33.1, "52W_H": 3200.0, "52W_L": 2300.0, "5Y_H": 3200.0, "5Y_L": 1200.0},
    "SRF": {"Industry": "Chemicals", "Promoter%": 50.5, "PE": 41.2, "Ind_PE": 34.0, "PB": 5.4, "ROCE": 17.2, "52W_H": 2700.0, "52W_L": 2100.0, "5Y_H": 2850.0, "5Y_L": 700.0},
    "LUPIN": {"Industry": "Pharmaceuticals", "Promoter%": 47.1, "PE": 38.5, "Ind_PE": 31.8, "PB": 4.1, "ROCE": 13.9, "52W_H": 1800.0, "52W_L": 900.0, "5Y_H": 1800.0, "5Y_L": 550.0},
    "AUROPHARMA": {"Industry": "Pharmaceuticals", "Promoter%": 51.8, "PE": 21.2, "Ind_PE": 31.8, "PB": 2.8, "ROCE": 14.2, "52W_H": 1450.0, "52W_L": 700.0, "5Y_H": 1450.0, "5Y_L": 400.0},
    "BALKRISIND": {"Industry": "Automobile", "Promoter%": 58.3, "PE": 34.6, "Ind_PE": 26.8, "PB": 5.9, "ROCE": 18.4, "52W_H": 3300.0, "52W_L": 2200.0, "5Y_H": 3300.0, "5Y_L": 750.0},
    "ASHOKLEY": {"Industry": "Automobile", "Promoter%": 51.5, "PE": 24.2, "Ind_PE": 26.8, "PB": 4.1, "ROCE": 15.3, "52W_H": 240.0, "52W_L": 140.0, "5Y_H": 240.0, "5Y_L": 40.0},
    "CHOLAFIN": {"Industry": "Banking & Finance", "Promoter%": 50.4, "PE": 31.8, "Ind_PE": 24.5, "PB": 5.2, "ROCE": 12.4, "52W_H": 1550.0, "52W_L": 1000.0, "5Y_H": 1550.0, "5Y_L": 250.0},
    "AUBANK": {"Industry": "Banking & Finance", "Promoter%": 25.4, "PE": 29.5, "Ind_PE": 15.2, "PB": 3.4, "ROCE": 10.9, "52W_H": 800.0, "52W_L": 560.0, "5Y_H": 800.0, "5Y_L": 350.0},
    "MUTHOOTFIN": {"Industry": "Banking & Finance", "Promoter%": 73.4, "PE": 16.2, "Ind_PE": 24.5, "PB": 2.8, "ROCE": 13.5, "52W_H": 1900.0, "52W_L": 1150.0, "5Y_H": 1900.0, "5Y_L": 500.0},
    "PERSISTENT": {"Industry": "Information Technology", "Promoter%": 31.1, "PE": 54.2, "Ind_PE": 28.1, "PB": 11.4, "ROCE": 31.2, "52W_H": 4950.0, "52W_L": 2800.0, "5Y_H": 4950.0, "5Y_L": 300.0},
    "COFORGE": {"Industry": "Information Technology", "Promoter%": 0.0, "PE": 48.9, "Ind_PE": 28.1, "PB": 9.1, "ROCE": 24.3, "52W_H": 6800.0, "52W_L": 4200.0, "5Y_H": 6800.0, "5Y_L": 900.0},
    "MPHASIS": {"Industry": "Information Technology", "Promoter%": 55.4, "PE": 27.2, "Ind_PE": 28.1, "PB": 5.1, "ROCE": 22.8, "52W_H": 2800.0, "52W_L": 1900.0, "5Y_H": 3400.0, "5Y_L": 700.0},
    "COLPAL": {"Industry": "FMCG", "Promoter%": 51.0, "PE": 58.4, "Ind_PE": 44.3, "PB": 41.2, "ROCE": 92.4, "52W_H": 3100.0, "52W_L": 1800.0, "5Y_H": 3100.0, "5Y_L": 1200.0},
    "MARICO": {"Industry": "FMCG", "Promoter%": 59.4, "PE": 44.5, "Ind_PE": 44.3, "PB": 14.8, "ROCE": 42.1, "52W_H": 680.0, "52W_L": 500.0, "5Y_H": 680.0, "5Y_L": 280.0},
    "GODREJCP": {"Industry": "FMCG", "Promoter%": 63.2, "PE": 61.2, "Ind_PE": 44.3, "PB": 10.1, "ROCE": 21.5, "52W_H": 1400.0, "52W_L": 950.0, "5Y_H": 1400.0, "5Y_L": 500.0},
    "BERGEPAINT": {"Industry": "Consumer Goods", "Promoter%": 75.0, "PE": 52.8, "Ind_PE": 51.1, "PB": 12.1, "ROCE": 24.8, "52W_H": 680.0, "52W_L": 450.0, "5Y_H": 850.0, "5Y_L": 300.0},
    "RVNL": {"Industry": "Defense & Capital Goods", "Promoter%": 72.8, "PE": 49.2, "Ind_PE": 42.1, "PB": 7.8, "ROCE": 17.4, "52W_H": 640.0, "52W_L": 110.0, "5Y_H": 640.0, "5Y_L": 15.0},
    "IRCTC": {"Industry": "Infrastructure", "Promoter%": 62.4, "PE": 64.5, "Ind_PE": 28.4, "PB": 14.2, "ROCE": 44.1, "52W_H": 1150.0, "52W_L": 640.0, "5Y_H": 1270.0, "5Y_L": 150.0},
    "BHEL": {"Industry": "Defense & Capital Goods", "Promoter%": 63.2, "PE": 110.4, "Ind_PE": 42.1, "PB": 4.1, "ROCE": 2.1, "52W_H": 330.0, "52W_L": 90.0, "5Y_H": 330.0, "5Y_L": 30.0},
    "OBEROIRLTY": {"Industry": "Infrastructure", "Promoter%": 67.7, "PE": 32.4, "Ind_PE": 28.4, "PB": 4.2, "ROCE": 11.5, "52W_H": 1950.0, "52W_L": 1100.0, "5Y_H": 1950.0, "5Y_L": 350.0},
    "YESBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 55.2, "Ind_PE": 15.2, "PB": 1.4, "ROCE": 5.8, "52W_H": 32.0, "52W_L": 15.0, "5Y_H": 85.0, "5Y_L": 10.0},
    "IDFCFIRSTB": {"Industry": "Banking & Finance", "Promoter%": 35.4, "PE": 19.8, "Ind_PE": 15.2, "PB": 1.5, "ROCE": 7.2, "52W_H": 100.0, "52W_L": 72.0, "5Y_H": 100.0, "5Y_L": 20.0},
    "GMRINFRA": {"Industry": "Infrastructure", "Promoter%": 59.1, "PE": 98.4, "Ind_PE": 28.4, "PB": 5.1, "ROCE": 8.1, "52W_H": 105.0, "52W_L": 42.0, "5Y_H": 105.0, "5Y_L": 15.0},
    "NMDC": {"Industry": "Metals & Mining", "Promoter%": 60.8, "PE": 14.1, "Ind_PE": 18.9, "PB": 2.4, "ROCE": 27.5, "52W_H": 280.0, "52W_L": 105.0, "5Y_H": 280.0, "5Y_L": 60.0},
    "SAIL": {"Industry": "Metals & Mining", "Promoter%": 65.0, "PE": 17.5, "Ind_PE": 18.9, "PB": 1.2, "ROCE": 9.4, "52W_H": 175.0, "52W_L": 82.0, "5Y_H": 175.0, "5Y_L": 25.0},
    "DEEPAKNTR": {"Industry": "Chemicals", "Promoter%": 45.7, "PE": 38.2, "Ind_PE": 34.0, "PB": 6.8, "ROCE": 22.4, "52W_H": 2600.0, "52W_L": 1800.0, "5Y_H": 3000.0, "5Y_L": 450.0},
}

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # 50-Length indicators maintained for Volume and Trend filters
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="900s")
def run_integrated_pipeline():
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    nifty_200_symbols = list(STOCK_METADATA.keys())
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(nifty_200_symbols)
    
    for index, symbol in enumerate(nifty_200_symbols):
        status_text.text(f"Syncing Nifty 200 Pipeline {index + 1}/{total_stocks}: {symbol}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        token = token_lookup.get(symbol)
        if not token:
            continue
        
        try:
            # Fetch 15-Minute Structural Frame
            hist_15m = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            # Fetch 1-Day Macro Frame
            hist_1d = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="day"
            )
            
            if not hist_15m or len(hist_15m) < 110 or not hist_1d or len(hist_1d) < 110:
                continue
                
            df_15m = pd.DataFrame(hist_15m)
            df_15m = calculate_indicators(df_15m)
            latest_15m = df_15m.iloc[-1]
            
            df_1d = pd.DataFrame(hist_1d)
            df_1d = calculate_indicators(df_1d)
            latest_1d =
