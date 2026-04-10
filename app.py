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
        if data: return data
        return {"orders": ["A001", "A002"]}
    except: return {"orders": ["A001", "A002"]}

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

if "user" not in st.session_state:
    st.title("⚓ 超慧科技●神鬼奇航●派工系統")
    user_list = get_users()
    u = st.selectbox("請選擇您的姓名", user_list)
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入系統", use_container_width=True):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"## 👤 當前操作者\n# {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["📝 現場派工作業", "📋 歷史派工紀錄", "⚙️ 選單內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    current_settings = get_settings()
    user_list = get_users()

    # --- 3. 現場派工作業 (位置微調) ---
    if menu == "📝 現場派工作業":
        # 修改大標題字體
        st.markdown("# ⚓ 超慧科技●神鬼奇航●派工系統")
        
        with st.form("dispatch_form"):
            st.subheader("📌 派工詳細資訊")
            
            # 第一列：將「選擇製令編號」與「作業期限」放在一起
            row1_col1, row1_col2 = st.columns(2)
            
            order_options = current_settings.get("orders", ["請先至後台設定製令"])
            order_no = row1_col1.selectbox("選擇製令編號", order_options)
            
            # 作業期限移動到這裡
            deadline = row1_col2.date_input("作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            # 第二列：派工人員與作業人員
            row2_col1, row2_col2 = st.columns(2)
            assigner = row2_col1.selectbox("派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = row2_col2.selectbox("作業人員", user_list)
            
            st.write("---")
            
            if st.form_submit_button("🚀 提交派工紀錄", use_container_width=True):
                dispatch_data = {
                    "提交者": st.session_state.user,
                    "製令": order_no,
                    "派工人員": assigner,
                    "作業人員": worker,
                    "作業期限": str(deadline),
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=dispatch_data)
                st.success(f"✅ 製令 {order_no} 派工成功！")

    # --- 4. 歷史派工紀錄 ---
    elif menu == "📋 歷史派工紀錄":
        st.header("📋 歷史派工紀錄查詢")
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                # 確保舊資料與新資料欄位大對齊
                display_cols = ["提交時間", "製令", "派工人員", "作業人員", "作業期限"]
                existing_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[existing_cols].sort_values(by="提交時間", ascending=False), use_container_width=True)
            else:
                st.info("目前尚無紀錄。")
        except: st.error("讀取紀錄失敗")

    # --- 5. 選單內容管理 ---
    elif menu == "⚙️ 選單內容管理":
        st.header("⚙️ 選單內容管理後台")
        with st.form("setting_orders"):
            st.subheader("📦 製令選單管理")
            existing_orders = ",".join(current_settings.get("orders", []))
            new_orders_str = st.text_area("編輯製令清單 (請用英文逗號 , 隔開)", value=existing_orders)
            
            if st.form_submit_button("儲存製令設定"):
                new_orders_list = [x.strip() for x in new_orders_str.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"orders": new_orders_list})
                st.success("✅ 製令清單已更新！")
                st.rerun()
