import streamlit as st
import pandas as pd
import requests
import hmac
import hashlib
import time

st.set_page_config(page_title="Delta Trading Journal", page_icon="📈", layout="wide")

st.title("📊 Delta Advanced Trading Journal")

# Sidebar - API Settings
st.sidebar.header("🔑 Delta API Settings")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("API Secret", type="password")
base_url = st.sidebar.selectbox("Exchange URL", ["https://cdn.india.delta.exchange", "https://api.delta.exchange"])

def get_signature(secret, message):
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

def call_delta_api(endpoint, key, secret, url):
    timestamp = str(int(time.time()))
    message = "GET" + timestamp + endpoint
    signature = get_signature(secret, message)
    headers = {
        'api-key': key,
        'signature': signature,
        'timestamp': timestamp,
        'Content-Type': 'application/json'
    }
    try:
        res = requests.get(url + endpoint, headers=headers, timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

if api_key and api_secret:
    if st.sidebar.button("🔄 Sync Live Data"):
        st.session_state['synced'] = True

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Trade History", "💰 Wallet & Cashflow"])

    # Fetch Trades
    fills_data = call_delta_api("/v2/fills", api_key, api_secret, base_url)
    trades = fills_data.get('result', []) if fills_data else []

    # Fetch Wallet
    wallet_data = call_delta_api("/v2/wallet/transactions", api_key, api_secret, base_url)
    txns = wallet_data.get('result', []) if wallet_data else []

    with tab1:
        st.subheader("Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        total_trades = len(trades)
        col1.metric("Total Trades", total_trades)
        
        if trades:
            df_trades = pd.DataFrame(trades)
            total_fee = df_trades['fee'].astype(float).sum() if 'fee' in df_trades else 0.0
            col2.metric("Total Fees Paid", f"${total_fee:.2f}")
        else:
            col2.metric("Total Fees Paid", "$0.00")
            
        col3.metric("Win Rate", "Live Tracked")
        col4.metric("Status", "API Connected 🟢")

    with tab2:
        st.subheader("Executed Orders & Fills")
        if trades:
            df_t = pd.DataFrame(trades)
            show_cols = [c for c in ['created_at', 'symbol', 'side', 'size', 'price', 'fee'] if c in df_t.columns]
            st.dataframe(df_t[show_cols], use_container_width=True)
        else:
            st.info("Koi recent trade nahi mila ya data load ho raha hai.")

    with tab3:
        st.subheader("Deposits & Withdrawals")
        if txns:
            df_w = pd.DataFrame(txns)
            st.dataframe(df_w, use_container_width=True)
        else:
            st.info("Koi wallet transaction record nahi mila.")
else:
    st.warning("👈 Left side menu me apni Delta Exchange ki Read-Only API Key aur Secret dalein.")
