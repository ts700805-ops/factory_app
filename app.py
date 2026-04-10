import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json")
        data = r.json()
        if not data: 
            return {"orders": [], "users": ["管理員", "賴智文"], "processes": ["預設工序"]}
        # 確保所有 key 都存在
        if "users" not in data: data["users"] = ["管理員", "賴智文"]
        if "orders" not in data: data["orders"] = []
        if "processes" not in data: data["processes"] = ["組裝", "測試"]
        return data
    except:
        return {"orders": [], "users": ["管理員", "賴智文"], "processes": ["預設工序"]}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; }
    .stat-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-top: 5px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    .stButton>button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings["users"])
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
                all_logs = []
                for k, v in data.items():
                    all_logs.append({
                        "製令": v.get("製令", "無"),
                        "製造工序": v.get("製造工序", "無"), # 新增欄位
                        "派工人員": v.get("派工人員", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", "無")
                    })
                df = pd.DataFrame(all_logs)
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                st.write("")
                st.subheader("📑 派工明細清單")
                st.dataframe(df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True, height=500)
            else: st.info("目前尚無派工資料。")
        except: st.error("連線資料庫失敗")

    # --- 4. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", settings["orders"])
            process_name = st.selectbox("⚙️ 選擇製造工序", settings["processes"]) # 新增下拉選單
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", settings["users"], index=settings["users"].index(st.session_state.user) if st.session_state.user in settings["users"] else 0)
            worker = c2.selectbox("👷 作業人員", settings["users"])
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務"):
                log = {
                    "製令": order_no, 
                    "製造工序": process_name, # 存入資料庫
                    "派工人員": assigner, 
                    "作業人員": worker, 
                    "作業期限": str(deadline), 
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已發布！")

    # --- 5. 📋 歷史紀錄查詢 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = []
                for k, v in db_data.items():
                    all_logs.append({
                        "id": k,
                        "製令": v.get("製令", "無"),
                        "製造工序": v.get("製造工序", "無"),
                        "派工人員": v.get("派工人員", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", str(datetime.date.today()))
                    })
                df = pd.DataFrame(all_logs)
                st.subheader("🔍 當前紀錄清單")
                st.dataframe(df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True)
                st.write("---")
                
                st.subheader("🛠️ 紀錄維護工具")
                log_options = {log['id']: f"【{log['製令']} - {log['製造工序']}】 作業：{log['作業人員']}" for log in all_logs}
                target_id = st.selectbox("請選擇要編輯或刪除的紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next(item for item in all_logs if item["id"] == target_id)
                
                with st.expander("📝 編輯此筆內容"):
                    ec1, ec2 = st.columns(2)
                    new_order = ec1.selectbox("修改製令", settings["orders"], index=settings["orders"].index(curr['製令']) if curr['製令'] in settings["orders"] else 0)
                    new_proc = ec2.selectbox("修改工序", settings["processes"], index=settings["processes"].index(curr['製造工序']) if curr['製造工序'] in settings["processes"] else 0)
                    
                    ec3, ec4, ec5 = st.columns(3)
                    new_a = ec3.selectbox("編輯派工員", settings["users"], index=settings["users"].index(curr['派工人員']) if curr['派工人員'] in settings["users"] else 0)
                    new_w = ec4.selectbox("編輯作業員", settings["users"], index=settings["users"].index(curr['作業人員']) if curr['作業人員'] in settings["users"] else 0)
                    try: d_val = datetime.datetime.strptime(curr['作業期限'], '%Y-%m-%d').date()
                    except: d_val = datetime.date.today()
                    new_d = ec5.date_input("編輯期限", d_val)
                    
                    if st.button("💾 儲存修改"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": new_order, "製造工序": new_proc, "派工人員": new_a, "作業人員": new_w, "作業期限": str(new_d)})
                        st.success("更新完成！")
                        st.rerun()
                if st.button("🗑️ 刪除選定紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.rerun()
            else: st.info("目前沒有紀錄。")
        except Exception as e: st.error(f"系統異常: {e}")

    # --- 6. ⚙️ 系統內容管理 (新增 製造工序 管理) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            # A. 製令清單
            st.subheader("📦 編輯製令清單")
            ex_orders = ",".join(settings.get("orders", []))
            new_orders = st.text_area("請用逗號隔開", value=ex_orders, height=100, key="o_a")
            
            # B. 人員清單
            st.subheader("👤 編輯人員清單")
            ex_users = ",".join(settings.get("users", []))
            new_users = st.text_area("請用逗號隔開", value=ex_users, height=100, key="u_a")
            
            # C. 新增：製造工序清單
            st.subheader("⚙️ 編輯製造工序清單")
            ex_procs = ",".join(settings.get("processes", ["組裝", "測試"]))
            new_procs = st.text_area("請用逗號隔開 (例如: 組裝,測試,包裝,品檢)", value=ex_procs, height=100, key="p_a")
            
            if st.form_submit_button("✅ 儲存並更新所有設定"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "users": [x.strip() for x in new_users.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_procs.split(",") if x.strip()]
                })
                st.success("後台設定已全面更新！")
                st.rerun()
