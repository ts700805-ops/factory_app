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
    .stButton>button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    user_list = get_users()
    u = st.selectbox("登入者姓名", user_list)
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "📋 歷史紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                # 使用 .get() 確保舊資料沒欄位時不會報錯
                all_logs = []
                for k, v in data.items():
                    all_logs.append({
                        "製令": v.get("製令", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", "無"),
                        "提交時間": v.get("提交時間", "")
                    })
                df = pd.DataFrame(all_logs)
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                st.write("")
                st.subheader("📑 派工明細清單")
                st.dataframe(df[["製令", "作業人員", "作業期限"]], use_container_width=True, height=500)
            else:
                st.info("目前尚無派工資料。")
        except: st.error("連線資料庫失敗")

    # --- 4. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        current_settings = get_settings()
        user_list = get_users()
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", current_settings.get("orders", ["(請先設定選單)"]))
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = c2.selectbox("👷 作業人員", user_list)
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已發布！")

    # --- 5. 📋 歷史紀錄查詢 (解決欄位缺失報錯問題) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                # 【重要修正】：使用 .get 避免 KeyError: '製令'
                all_logs = []
                for k, v in db_data.items():
                    all_logs.append({
                        "id": k,
                        "製令": v.get("製令", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", str(datetime.date.today()))
                    })
                
                df = pd.DataFrame(all_logs)
                
                st.subheader("🔍 當前紀錄清單")
                st.dataframe(df[["製令", "作業人員", "作業期限"]], use_container_width=True)
                
                st.write("---")
                
                st.subheader("🛠️ 紀錄維護工具")
                # 下拉選單顯示
                log_options = {log['id']: f"製令：{log['製令']} | 人員：{log['作業人員']} | 期限：{log['作業期限']}" for log in all_logs}
                
                target_id = st.selectbox("請選擇要編輯或刪除的紀錄", 
                                       options=list(log_options.keys()), 
                                       format_func=lambda x: log_options[x])
                
                current_log = next(item for item in all_logs if item["id"] == target_id)
                
                with st.expander("📝 編輯此筆內容", expanded=False):
                    ec1, ec2 = st.columns(2)
                    current_w = current_log['作業人員']
                    new_w = ec1.selectbox("更換作業人員", get_users(), 
                                       index=get_users().index(current_w) if current_w in get_users() else 0)
                    
                    # 處理日期格式容錯
                    try:
                        d_val = datetime.datetime.strptime(current_log['作業期限'], '%Y-%m-%d').date()
                    except:
                        d_val = datetime.date.today()
                        
                    new_d = ec2.date_input("更換作業期限", d_val)
                    
                    if st.button("💾 儲存修改"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"作業人員": new_w, "作業期限": str(new_d)})
                        st.success("更新成功！")
                        st.rerun()

                if st.button("🗑️ 刪除選定紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.warning("紀錄已刪除。")
                    st.rerun()
            else:
                st.info("目前沒有紀錄。")
        except Exception as e:
            st.error(f"讀取資料發生錯誤: {e}")

    # --- 6. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        current_settings = get_settings()
        with st.form("fav_edit"):
            existing_str = ",".join(current_settings.get("orders", []))
            new_orders_raw = st.text_area("編輯製令清單 (用逗號隔開)", value=existing_str, height=200)
            if st.form_submit_button("✅ 儲存並更新"):
                new_list = [x.strip() for x in new_orders_raw.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"orders": new_list})
                st.success("更新成功！")
                st.rerun()
