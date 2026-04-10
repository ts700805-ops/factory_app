import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
USER_DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/users"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_users():
    try:
        r = requests.get(f"{USER_DB_URL}.json")
        data = r.json()
        if data and isinstance(data, dict): return list(data.keys())
        return ["管理員", "李小龍", "賴智文", "黃沂澂"]
    except: return ["管理員", "李小龍", "賴智文", "黃沂澂"]

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技派工管理系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 現場派工管理系統 - 登入")
    user_list = get_users()
    u = st.selectbox("請選擇您的姓名", user_list)
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入系統", use_container_width=True):
        # 這裡簡化驗證邏輯，僅示範登入成功
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"## 👤 當前操作者\n# {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["📝 現場派工作業", "📋 歷史派工紀錄"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 現場派工作業 (依照要求修改格式) ---
    if menu == "📝 現場派工作業":
        st.header("📝 新增現場派工單")
        
        # 移除計時器工具，直接進入派工表單
        with st.form("dispatch_form"):
            st.subheader("📌 派工詳細資訊")
            
            # 第一列：製令
            order_no = st.text_input("製令編號", placeholder="請輸入製令單號")
            
            # 第二列：派工與作業人員
            user_list = get_users()
            col1, col2 = st.columns(2)
            assigner = col1.selectbox("派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = col2.selectbox("作業人員", user_list)
            
            # 第三列：作業期限 (可自行點選日期)
            deadline = st.date_input("作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            st.write("---")
            
            # 提交按鈕
            if st.form_submit_button("🚀 提交派工紀錄", use_container_width=True):
                if order_no:
                    # 建立存檔資料 (僅保留要求的欄位)
                    dispatch_data = {
                        "提交者": st.session_state.user,
                        "製令": order_no,
                        "派工人員": assigner,
                        "作業人員": worker,
                        "作業期限": str(deadline),
                        "提交時間": get_now_str()
                    }
                    
                    # 永久存入雲端 Firebase
                    requests.post(f"{DB_URL}.json", json=dispatch_data)
                    st.success(f"✅ 製令 {order_no} 派工成功！資料已永久存檔。")
                else:
                    st.error("❌ 請輸入製令編號後再提交。")

    # --- 4. 歷史派工紀錄 (查看永久存檔) ---
    elif menu == "📋 歷史派工紀錄":
        st.header("📋 歷史派工紀錄查詢")
        
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                raw_rows = []
                for k, v in data.items():
                    row = {"id": k}
                    row.update(v)
                    raw_rows.append(row)
                
                df = pd.DataFrame(raw_rows)
                
                # 整理顯示順序
                display_cols = ["提交時間", "製令", "派工人員", "作業人員", "作業期限"]
                existing_cols = [c for c in display_cols if c in df.columns]
                
                st.dataframe(df[existing_cols].sort_values(by="提交時間", ascending=False), use_container_width=True)
            else:
                st.info("目前尚無派工紀錄。")
        except Exception as e:
            st.error(f"讀取紀錄失敗：{e}")
