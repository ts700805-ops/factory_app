import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
USER_DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/users"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_users():
    try:
        r = requests.get(f"{USER_DB_URL}.json")
        data = r.json()
        if data and isinstance(data, dict): return list(data.keys())
        return ["管理員", "賴智文", "黃沂澂"]
    except: return ["管理員", "賴智文", "黃沂澂"]

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json")
        data = r.json()
        return data if data else {"orders": []}
    except: return {"orders": []}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

# 自定義專業 CSS 樣式
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; }
    .stat-card { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    user_list = get_users()
    u = st.selectbox("登入者姓名", user_list)
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航", use_container_width=True):
        st.session_state.user = u
        st.rerun()
else:
    # 側邊欄選單
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "📋 歷史紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (專為老闆設計的主頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                
                # 數據統計指標
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="stat-card">總派工件數<br><span style="font-size:30px;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    today_count = len(df[df['提交時間'].str.contains(datetime.date.today().strftime("%Y-%m-%d"))]) if '提交時間' in df.columns else 0
                    st.markdown(f'<div class="stat-card">今日新增<br><span style="font-size:30px;">{today_count}</span> 件</div>', unsafe_allow_html=True)
                with c3:
                    worker_count = df['作業人員'].nunique() if '作業人員' in df.columns else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:30px;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                st.write("---")
                
                # 專業表格顯示
                st.subheader("📑 即時派工明細")
                display_df = df[["提交時間", "製令", "派工人員", "作業人員", "作業期限"]].sort_values(by="提交時間", ascending=False)
                st.dataframe(display_df, use_container_width=True, height=500)
                
            else:
                st.info("⚓ 航道清空，目前尚無派工資料。")
        except:
            st.error("讀取雲端資料庫時發生通訊錯誤。")

    # --- 4. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        current_settings = get_settings()
        user_list = get_users()
        
        with st.form("dispatch_form"):
            order_options = current_settings.get("orders", ["(請至管理頁面設定製令)"])
            order_no = st.selectbox("📦 選擇製令編號", order_options)
            
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = c2.selectbox("👷 作業人員", user_list)
            
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.form_submit_button("🚀 發布任務並存檔", use_container_width=True):
                log = {"提交者": st.session_state.user, "製令": order_no, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已同步至雲端，老闆已可看見。")

    # --- 5. 📋 歷史紀錄查詢 (含刪除功能) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄管理")
        # (這裡放原本的查詢與刪除邏輯...)
        st.write("目前資料已顯示於看板，此處可進行維護。")

    # --- 6. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統選單設定")
        current_settings = get_settings()
        with st.form("set_orders"):
            existing = ",".join(current_settings.get("orders", []))
            raw = st.text_area("編輯下拉選單內容 (用逗號隔開)", value=existing)
            if st.form_submit_button("儲存並更新選單"):
                new_list = [x.strip() for x in raw.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"orders": new_list})
                st.rerun()
