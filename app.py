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

# --- 2. 頁面配置 (優化字體大小以增加顯示筆數) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●管理系統", layout="wide")

st.markdown("""
    <style>
    /* 全局背景與字體微調 */
    .main { background-color: #f8f9fa; }
    
    /* 列表區塊字體縮小：讓人員看到更多筆資料 */
    .task-row {
        background-color: white;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .task-info-main {
        font-size: 22px !important; /* 縮小主要標題 */
        font-weight: bold;
        color: #1E3A8A;
    }
    .task-info-sub {
        font-size: 16px !important; /* 縮小次要資訊 */
        color: #555;
    }

    /* 篩選與輸入框標籤縮小 */
    .stSelectbox label, .stDateInput label { font-size: 16px !important; font-weight: bold !important; }
    
    /* 完工按鈕縮小 */
    .stButton>button {
        height: 40px !important;
        font-size: 18px !important;
        padding: 0px 20px !important;
    }
    
    /* 標題與統計卡片 */
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 3px solid #1E3A8A; margin-bottom: 15px; }
    .stat-card { background-color: #ffffff; padding: 10px; border-radius: 10px; border-top: 4px solid #1E3A8A; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.balloons()
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "✅ 完工紀錄專區", "📝 現場派工作業", "📋 歷史紀錄維護", "⚙️ 系統內容管理"])
    
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
                    v['id'] = k
                    all_logs.append(v)
                df = pd.DataFrame(all_logs)

                # 統計數據
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:30px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:30px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                # 篩選功能
                with st.expander("🔍 快速篩選資料", expanded=True):
                    f1, f2, f3, f4 = st.columns(4)
                    sel_order = f1.selectbox("按製令", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員", ["全部"] + sorted(df["派工人員"].unique().tolist()))
                    sel_worker = f4.selectbox("按作業員", ["全部"] + sorted(df["作業人員"].unique().tolist()))

                f_df = df.copy()
                if sel_order != "全部": f_df = f_df[f_df["製令"] == sel_order]
                if sel_process != "全部": f_df = f_df[f_df["製造工序"] == sel_process]
                if sel_assigner != "全部": f_df = f_df[f_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": f_df = f_df[f_df["作業人員"] == sel_worker]

                st.subheader("📑 待辦派工明細 (點擊按鈕結案)") 
                for index, row in f_df.iterrows():
                    with st.container():
                        # 緊湊排列：資訊佔 8 份，按鈕佔 1 份
                        col_info, col_btn = st.columns([8, 1])
                        with col_info:
                            st.markdown(f"""
                            <div class="task-row">
                                <span class="task-info-main">📦 {row.get('製令')} | 👷 {row.get('作業人員')}</span><br>
                                <span class="task-info-sub">⚙️ 工序：{row.get('製造工序')} | ⏳ 期限：{row.get('作業期限')} | 🚩 派工：{row.get('派工人員')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_btn:
                            st.write("") # 微調對齊
                            if st.button("✅ 完工", key=f"btn_{row['id']}"):
                                try:
                                    # 1. 搬移資料
                                    done_item = row.to_dict()
                                    done_item['實際完工時間'] = get_now_str()
                                    post_r = requests.post(f"{DONE_URL}.json", json=done_item)
                                    # 2. 刪除原資料
                                    if post_r.status_code == 200:
                                        requests.delete(f"{DB_URL}/{row['id']}.json")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error("完工紀錄存檔失敗，請檢查網路。")
                                except Exception as e:
                                    st.error(f"連線失敗: {e}")
            else: st.info("目前尚無待辦任務。")
        except: st.error("連線資料庫失敗，請確認 Firebase URL 設定正確。")

    # --- 4. ✅ 完工紀錄專區 ---
    elif menu == "✅ 完工紀錄專區":
        st.markdown('<p class="main-title">✅ 已完工任務清單</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DONE_URL}.json")
            done_data = r.json()
            if done_data:
                df_done = pd.DataFrame([v for k, v in done_data.items()])
                if '實際完工時間' in df_done.columns:
                    df_done = df_done.sort_values(by='實際完工時間', ascending=False)
                st.dataframe(df_done[["製令", "製造工序", "作業人員", "實際完工時間", "派工人員"]], use_container_width=True, hide_index=True)
            else: st.info("目前尚無完工資料。")
        except: st.error("讀取完工資料失敗。")

    # --- 5. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form", clear_on_submit=True):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            c1, c2 = st.columns(2)
            # 自動鎖定目前登入者為派工人員
            assigner = c1.selectbox("🚩 派工人員", settings.get("assigners", []), 
                                    index=settings.get("assigners", []).index(st.session_state.user) if st.session_state.user in settings.get("assigners", []) else 0)
            worker = c2.selectbox("👷 作業人員", settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.form_submit_button("🚀 發布派工任務"):
                new_log = {
                    "製令": order_no,
                    "製造工序": process_name,
                    "派工人員": assigner,
                    "作業人員": worker,
                    "作業期限": str(deadline),
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=new_log)
                st.balloons()
                st.success(f"任務已發布給 {worker}！")

    # --- 6. 📋 歷史紀錄維護 ---
    elif menu == "📋 歷史紀錄維護":
        st.header("📋 待辦紀錄管理與修正")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [{"id": k, **v} for k, v in db_data.items()]
                df_edit = pd.DataFrame(all_logs)
                st.dataframe(df_edit[["製令", "製造工序", "作業人員", "作業期限"]], use_container_width=True, hide_index=True)
                
                st.divider()
                target_id = st.selectbox("選擇要處理的 ID", [item['id'] for item in all_logs])
                curr = next(i for i in all_logs if i['id'] == target_id)
                
                with st.expander("🛠️ 修改此筆資料內容"):
                    new_w = st.selectbox("更改作業員", settings.get("workers", []), index=settings.get("workers", []).index(curr['作業人員']) if curr['作業人員'] in settings.get("workers", []) else 0)
                    new_d = st.date_input("更改期限", datetime.datetime.strptime(curr['作業期限'], '%Y-%m-%d').date() if '-' in curr['作業期限'] else datetime.date.today())
                    if st.button("💾 儲存修改內容"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"作業人員": new_w, "作業期限": str(new_d)})
                        st.success("修改成功！")
                        st.rerun()
                
                if st.button("🗑️ 刪除此筆任務", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.warning("紀錄已刪除。")
                    st.rerun()
            else: st.info("目前沒有可編輯的待辦任務。")
        except: st.error("資料獲取失敗。")

    # --- 7. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 下拉選單資料管理")
        with st.form("settings_form"):
            st.subheader("📦 製令清單 (以逗號隔開)")
            new_orders = st.text_area("製令", value=",".join(settings.get("orders", [])), height=100)
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🚩 派工人員清單")
                new_assigners = st.text_area("管理員", value=",".join(settings.get("assigners", [])), height=150)
            with c2:
                st.subheader("👷 作業人員清單")
                new_workers = st.text_area("現場人員", value=",".join(settings.get("workers", [])), height=150)
            
            st.subheader("⚙️ 製造工序清單")
            new_procs = st.text_area("工序", value=",".join(settings.get("processes", [])), height=100)
            
            if st.form_submit_button("✅ 儲存系統設定"):
                updated_settings = {
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "workers": [x.strip() for x in new_workers.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_procs.split(",") if x.strip()]
                }
                requests.patch(f"{SETTING_URL}.json", json=updated_settings)
                st.success("系統選單已更新！")
                st.rerun()
