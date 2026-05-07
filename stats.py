import streamlit as st
import pandas as pd
import requests
import json

# --- 設定資料庫路徑 (與 app.py 相同) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"

st.set_page_config(page_title="工時統計系統", layout="wide")

st.title("📊 工時統計分析系統")

# --- 讀取資料的函式 ---
def fetch_data():
    try:
        r = requests.get(f"{FINISH_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                # 將 Firebase 的字典格式轉換為 Pandas 表格
                df = pd.DataFrame([v for k, v in data.items()])
                return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"資料抓取失敗: {e}")
        return pd.DataFrame()

# --- 畫面呈現 ---
df = fetch_data()

if not df.empty:
    st.success("✅ 成功讀取完工紀錄！")
    
    # 這裡先顯示前 5 筆，確認資料抓得到
    st.subheader("最新完工資料預覽")
    st.dataframe(df.head(), use_container_width=True)
    
    # TODO: 接下來在這裡寫工時計算邏輯
else:
    st.warning("目前資料庫中沒有完工紀錄，或者連線失敗。")
