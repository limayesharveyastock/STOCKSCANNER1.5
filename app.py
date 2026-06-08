import streamlit as st
from kiteconnect import KiteConnect

st.title("API Diagnostic Tool")

api_key = st.secrets["api_key"]
access_token = st.secrets["access_token"]

if st.button("Test Connectivity"):
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        # Try fetching LTP for a liquid stock
        data = kite.ltp("NSE:RELIANCE")
        st.success(f"Connection Successful! Price: {data['NSE:RELIANCE']['last_price']}")
    except Exception as e:
        st.error(f"CONNECTION FAILED: {str(e)}")
        st.write("If you see 'TokenException', your access_token is expired. Generate a new one.")
