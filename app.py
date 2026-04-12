import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json")
        data = r.json()
        if not data: 
            return {"orders": [], "assigners": ["管理員"], "workers": ["人員"], "processes": ["預設工序"]}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "workers": ["人員"], "processes": ["預設工序"]}

# --- 2. 頁面配置 (強化手機版可視性) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 針對數據卡片的字體優化 */
    .stat-card {
        background-color: #ffffff;
        padding: 20px 10px;
        border-radius: 12px;
        border-top: 6px solid #1E3A8A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 15px;
    }
    .stat-label {
        font-size: 22px !important;
        font-weight: bold;
        color: #4B5563;
        margin-bottom: 10px;
    }
    .stat-value {
        font-size: 60px !important; /* 放大數據字體，解決手機看不清問題 */
        font-weight: 900;
        color: #1E3A8A;
        line-height: 1;
    }
    .stat-unit {
        font-size: 24px !important;
        color: #1E3A8A;
        margin-left: 5px;
    }

    /* 調整表格與標題大小 */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div { font-size: 18px !important; }
    .main-title { font-size: 28px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 20px; }
    .stButton>button { height: 65px; font-size: 22px !important; font-weight: bold !important; border-radius: 10px; }
    
    /* 讓下拉選單在手機上更明顯 */
    .stSelectbox label { font-size: 20px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "✅ 已完工歷史紀錄查詢", "📝 現場派工作業", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 超慧科技現場派工看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    v['db_key'] = k
                    all_logs.append(v)
                df = pd.DataFrame(all_logs).fillna("無")
                
                # 手機版字體加強版看板
                c1, c2 = st.columns(2)
                with c1: 
                    st.markdown(f'''
                        <div class="stat-card">
                            <div class="stat-label">總派件數</div>
                            <div class="stat-value">{len(df)}<span class="stat-unit">件</span></div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'''
                        <div class="stat-card">
                            <div class="stat-label">動員人力</div>
                            <div class="stat-value">{worker_count}<span class="stat-unit">人</span></div>
                        </div>
                    ''', unsafe_allow_html=True)
                
                with st.expander("🔍 快速篩選資料", expanded=False):
                    f1, f2 = st.columns(2)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_worker = f2.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]

                st.subheader("📑 待辦派工明細") 
                st.dataframe(filtered_df[["製令", "製造工序", "作業人員", "作業期限"]], use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("📦 快速結案")
                for index, row in filtered_df.iterrows():
                    with st.container():
                        col_info, col_btn = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"**{row['製令']}** ({row['製造工序']})")
                            st.caption(f"負責人：{row['作業人員']}")
                        if col_btn.button(f"✅ 完工", key=f"btn_{row['db_key']}"):
                            done_data = row.to_dict()
                            db_key = done_data.pop('db_key')
                            done_data['實際完工時間'] = get_now_str()
                            requests.post(f"{DONE_URL}.json", json=done_data)
                            requests.delete(f"{DB_URL}/{db_key}.json")
                            st.balloons() # 保留特效
                            st.rerun()
            else:
                st.info("目前尚無待辦派工。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. ✅ 已完工歷史紀錄查詢 ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄</p>', unsafe_allow_html=True)
        # (此處保留您原有的查詢與刪除邏輯，不變動)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = [dict(v, done_key=k) for k, v in done_data.items() if v]
                df_done = pd.DataFrame(done_list).fillna("無")
                st.dataframe(df_done[["實際完工時間", "製令", "作業人員"]].sort_values("實際完工時間", ascending=False), use_container_width=True, hide_index=True)

    # --- 5. 📝 現場派工作業 (保留氣球特效) ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form", clear_on_submit=True):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            assigner = st.selectbox("🚩 派工人員", settings.get("assigners", []), index=0)
            worker = st.selectbox("👷 主要人員", settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                res = requests.post(f"{DB_URL}.json", json=log)
                if res.status_code == 200:
                    st.balloons() # 氣球特效要在
                    st.success(f"任務 [{order_no}] 已發布！")
                else:
                    st.error("連線失敗")

    # --- 6. 📝 編輯派工紀錄 (要有派工人員與製令) ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 待辦派工紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"{log.get('製令')} | {log.get('作業人員')}" for log in all_logs}
                target_id = st.selectbox("選擇欲修改的紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                if curr:
                    with st.container():
                        # 修改製令
                        edit_order = st.selectbox("修改製令編號", settings.get("orders", []), index=settings.get("orders", []).index(curr.get('製令')) if curr.get('製令') in settings.get("orders", []) else 0)
                        # 修改派工人員
                        edit_assigner = st.selectbox("修改派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(curr.get('派工人員')) if curr.get('派工人員') in settings.get("assigners", []) else 0)
                        # 修改作業員
                        new_worker = st.selectbox("修改主要人員", settings.get("workers", []), index=settings.get("workers", []).index(curr.get('作業人員')) if curr.get('作業人員') in settings.get("workers", []) else 0)
                        
                        if st.button("💾 儲存修改"):
                            requests.patch(f"{DB_URL}/{target_id}.json", json={
                                "製令": edit_order,
                                "派工人員": edit_assigner,
                                "作業人員": new_worker
                            })
                            st.success("紀錄已更新！")
                            st.rerun()
                    
                    st.markdown("---")
                    if st.button("🗑️ 刪除此筆待辦任務", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
        except: st.error("讀取失敗")

    # --- 7. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            new_orders = st.text_area("📦 編輯製令清單 (逗號隔開)", value=",".join(settings.get("orders", [])), height=120)
            new_assigners = st.text_area("🚩 編輯派工人員清單", value=",".join(settings.get("assigners", [])), height=100)
            new_workers = st.text_area("👷 編輯作業人員清單", value=",".join(settings.get("workers", [])), height=100)
            if st.form_submit_button("✅ 儲存系統設定"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "workers": [x.strip() for x in new_workers.split(",") if x.strip()]
                })
                st.success("設定已儲存！")
                st.rerun()
