import streamlit as st
import pandas as pd
import datetime

# --- 介面設定 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

# 初始化 Session State
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "user" not in st.session_state:
    st.session_state.user = None

# --- 側邊欄導航 (修正縮排版) ---
def sidebar_nav():
    st.sidebar.markdown(f"### 👤 當前人員：**{st.session_state.user}**")
    
    # 這裡確保每一行都對齊，沒有混合使用 Tab 與空白
    options = [
        "💡 2026上半年技能考核進度", 
        "🧾 組長待辦事項",
        "🛡️ 🛡️ 🛡️ 🛡️ 🛡️ 🛡️",
        "📝 每日6S任務回報", 
        "🎮 6S戰境養成", 
        "🟢 6S個人能力查詢",
        "🛡️ 🛡️ 🛡️ 🛡️ 🛡️ 🛡️",
        "📊 製造部派工專區", 
        "📜 完工紀錄查詢", 
        "🔧 固資&手工具紀錄表",
        "⚙️ 資產編輯清單", 
        "⚙️ 設定管理"
    ]
    
    # 使用 index 參數來保持選擇狀態
    current_idx = options.index(st.session_state.menu_selection) if st.session_state.menu_selection in options else 0
    nav = st.sidebar.radio("功能導航", options, index=current_idx)
    
    # 登出按鈕
    if st.sidebar.button("🚪 點此登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    return nav

# --- 主程式流程 ---
if st.session_state.user is None:
    st.title("⚓ 登入系統")
    user = st.selectbox("請選擇組長", ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"])
    if st.button("確認登入"):
        st.session_state.user = user
        st.rerun()
else:
    # 執行導航
    nav = sidebar_nav()
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    # --- 頁面內容切換 ---
    st.title(f"目前檢視：{st.session_state.menu_selection}")

    if st.session_state.menu_selection == "🧾 組長待辦事項":
        st.subheader("待處理項目清單")
        
        # 範例資料
        data = {
            "狀態": ["🔴 緊急", "🟡 處理中", "🟢 已排程"],
            "任務名稱": ["設備異常排除", "員工技能核對", "庫存盤點"],
            "截止日期": ["2026-06-09", "2026-06-10", "2026-06-15"]
        }
        df = pd.DataFrame(data)
        st.table(df)
        
        if st.button("新增待辦事項"):
            st.info("功能開發中...")

    elif st.session_state.menu_selection == "📊 製造部派工專區":
        st.write("這裡是派工專區內容...")

    # 其他頁面依此類推...
