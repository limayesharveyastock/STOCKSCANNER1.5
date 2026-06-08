import os
import re
import pyotp
import toml
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- USER CONFIGURATION ---
# Replace these placeholders with your actual secure details
ZE_USER = "YOUR_ZERODHA_CLIENT_ID"
ZE_PASS = "YOUR_ZERODHA_PASSWORD"
ZE_TOTP_SECRET = "YOUR_2FA_TOTP_SECRET_KEY"  # The text string from Zerodha security settings

KITE_API_KEY = "YOUR_KITE_API_KEY"
KITE_API_SECRET = "YOUR_KITE_API_SECRET"
SECRETS_PATH = ".streamlit/secrets.toml"

def run_daily_handshake():
    print("🚀 Initiating automated market login handshake...")
    
    # 1. Initialize Kite Core
    kite = KiteConnect(api_key=KITE_API_KEY)
    login_url = kite.login_url()
    
    # 2. Configure Headless Chrome Browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs silently without popping a window open
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.implicitly_wait(10)
    
    try:
        # 3. Navigate to Zerodha's Secure Authorization gateway
        driver.get(login_url)
        
        # 4. Input Credentials
        driver.find_element(By.ID, "userid").send_keys(ZE_USER)
        driver.find_element(By.ID, "password").send_keys(ZE_PASS)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # 5. Generate and Input 2FA TOTP Token via pyotp
        print("🔐 Extrapolating 6-Digit 2FA Factor Token...")
        totp = pyotp.TOTP(ZE_TOTP_SECRET)
        current_token = totp.now()
        
        driver.find_element(By.ID, "userid").send_keys(current_token) # Kite DOM uses same ID for TOTP field sometimes or class-based tracking
        # Fallback element lookup selector if entry structure differs:
        # driver.find_element(By.XPATH, "//input[@type='number' or @placeholder='TOTP']").send_keys(current_token)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # 6. Intercept Redirect and Extract Request Token
        print("📡 Intercepting authorization response matrix...")
        # Wait a brief window for redirect loop to finish completing
        import time
        time.sleep(3)
        
        redirected_url = driver.current_url
        if "request_token=" not in redirected_url:
            raise Exception("Authentication redirection breakdown. Check login credentials.")
            
        request_token = re.search(r"request_token=([a-zA-Z0-9]+)", redirected_url).group(1)
        print(f"🎯 Request Token Captured successfully: {request_token[:5]}*****")
        
        # 7. Generate Daily Access Session via Kite API
        session = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        access_token = session["access_token"]
        print("🔥 Access Token successfully minted.")
        
        # 8. Safely write/update the local .streamlit/secrets.toml matrix file
        os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
        
        # Keep existing structural data intact if any exists, only rewrite target metrics
        existing_secrets = {}
        if os.path.exists(SECRETS_PATH):
            try:
                existing_secrets = toml.load(SECRETS_PATH)
            except Exception:
                pass
                
        existing_secrets["api_key"] = KITE_API_KEY
        existing_secrets["access_token"] = access_token
        
        with open(SECRETS_PATH, "w") as f:
            toml.dump(existing_secrets, f)
            
        print("✅ Secure `.streamlit/secrets.toml` file dynamically synchronized. System ready.")
        
    except Exception as e:
        print(f"❌ Automation Failure Chain: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_daily_handshake()
