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

st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; }
    .stat-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-top: 5px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
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
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "📋 歷史紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (老闆首頁 - 隱藏時間，強調總量) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                
                # 僅顯示 老闆要求的核心指標
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'<div class="stat-card"><span style="color:#666;">總派件數</span><br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> <span style="font-size:18px;">件</span></div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if '作業人員' in df.columns else 0
                    st.markdown(f'<div class="stat-card"><span style="color:#666;">動員人力</span><br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> <span style="font-size:18px;">人</span></div>', unsafe_allow_html=True)
                
                st.write("")
                
                # 表格移除提交時間，只顯示內容
                st.subheader("📑 派工明細清單")
                # 這裡移除 "提交時間" 欄位
                cols_to_show = ["製令", "派工人員", "作業人員", "作業期限"]
                display_df = df[[c for c in cols_to_show if c in df.columns]]
                st.dataframe(display_df, use_container_width=True, height=500)
                
            else:
                st.info("⚓ 目前尚無派工資料。")
        except:
            st.error("讀取失敗")

    # --- 4. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        current_settings = get_settings()
        user_list = get_users()
        
        with st.form("dispatch_form"):
            order_options = current_settings.get("orders", ["(請至管理頁面設定)"])
            order_no = st.selectbox("📦 選擇製令編號", order_options)
            
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = c2.selectbox("👷 作業人員", user_list)
            
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.form_submit_button("🚀 發布任務", use_container_width=True):
                log = {"製令": order_no, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已同步至雲端看板。")

    # --- 5. 📋 歷史紀錄查詢 (維護管理) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                st.dataframe(df, use_container_width=True)
                
                with st.expander("🗑️ 刪除紀錄"):
                    to_delete = st.selectbox("選擇要刪除的製令紀錄", df['id'].tolist())
                    if st.button("確認刪除"):
                        requests.delete(f"{DB_URL}/{to_delete}.json")
                        st.rerun()
        except: st.write("尚無紀錄")

    # --- 6. ⚙️ 系統內容管理 (新增編輯與刪除功能) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容控制台")
        current_settings = get_settings()
        orders = current_settings.get("orders", [])

        # A. 新增內容
        with st.expander("➕ 新增製令選項", expanded=True):
            new_order = st.text_input("輸入新製令編號")
            if st.button("加入選單"):
                if new_order and new_order not in orders:
                    orders.append(new_order)
                    requests.patch(f"{SETTING_URL}.json", json={"orders": orders})
                    st.success(f"已新增: {new_order}")
                    st.rerun()

        st.write("---")
        
        # B. 編輯與刪除現有內容
        st.subheader("📝 現有選單編輯")
        if not orders:
            st.info("目前選單是空的。")
        else:
            for i, ord_item in enumerate(orders):
                col_name, col_edit, col_del = st.columns([3, 2, 1])
                col_name.write(f"📦 {ord_item}")
                
                # 編輯功能
                new_val = col_edit.text_input("修改名稱", value=ord_item, key=f"edit_{i}")
                if new_val != ord_item:
                    if col_edit.button("儲存修改", key=f"save_{i}"):
                        orders[i] = new_val
                        requests.patch(f"{SETTING_URL}.json", json={"orders": orders})
                        st.rerun()
                
                # 刪除功能
                if col_del.button("🗑️ 刪除", key=f"del_{i}"):
                    orders.remove(ord_item)
                    requests.patch(f"{SETTING_URL}.json", json={"orders": orders})
                    st.rerun()
