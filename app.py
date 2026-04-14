import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (完全保留) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        data = r.json()
        if not data: 
            return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}
        if "worker_map" not in data: data["worker_map"] = {}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}

# --- 2. 頁面配置與 CSS 樣式 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 標題與基礎樣式 */
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 3px solid #1E3A8A; margin-bottom: 20px; }
    
    /* 統計卡片 */
    .stat-card { 
        background-color: #ffffff; padding: 10px; border-radius: 8px; border-top: 4px solid #1E3A8A; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; margin-bottom: 15px;
    }
    .stat-label { font-size: 16px; font-weight: bold; color: #64748b; }
    .stat-value { font-size: 28px; font-weight: bold; color: #1E3A8A; }

    /* 精緻條列樣式 */
    .list-row {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 8px solid #3b82f6; 
        padding: 12px 20px;
        border-radius: 6px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .list-item { flex: 1; text-align: left; }
    .item-label { font-size: 13px; color: #94a3b8; font-weight: normal; margin-bottom: 2px; }
    .item-value { font-size: 18px; color: #1e293b; font-weight: bold; }
    .badge {
        background: #dbeafe; color: #1e40af; padding: 4px 12px; 
        border-radius: 15px; font-size: 14px; font-weight: bold;
    }
    .date-text { color: #1E3A8A; }
    
    /* 選單字體 */
    .stSelectbox label { font-size: 18px !important; font-weight: bold !important; }
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
                    if v:
                        v['db_key'] = k
                        all_logs.append(v)
                df = pd.DataFrame(all_logs).fillna("無")
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card"><span class="stat-label">總派件數</span><br><span class="stat-value">{len(df)} 件</span></div>', unsafe_allow_html=True)
                with c2: 
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card"><span class="stat-label">動員人力</span><br><span class="stat-value">{worker_count} 人</span></div>', unsafe_allow_html=True)
                
                with st.expander("🔍 快速篩選資料", expanded=False):
                    f1, f2, f3 = st.columns(3)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序篩選", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員篩選", ["全部"] + sorted(df["派工人員"].unique().tolist()))
                    
                    f4, f5, f6 = st.columns(3)
                    sel_worker = f4.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))
                    sel_assistant = f5.selectbox("按協助人員篩選", ["全部"] + sorted(df["協助人員"].unique().tolist()))
                    sel_date = f6.selectbox("按派工日期篩選", ["全部"] + sorted(df["作業期限"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]
                if sel_assistant != "全部": filtered_df = filtered_df[filtered_df["協助人員"] == sel_assistant]
                if sel_date != "全部": filtered_df = filtered_df[filtered_df["作業期限"] == sel_date]

                st.subheader("📑 待辦派工明細清單")
                if filtered_df.empty:
                    st.info("查無符合條件之資料。")
                else:
                    for _, row in filtered_df.iterrows():
                        st.markdown(f"""
                        <div class="list-row">
                            <div class="list-item" style="flex: 1.5;">
                                <div class="item-label">製令編號</div>
                                <div class="item-value">📦 {row['製令']}</div>
                            </div>
                            <div class="list-item" style="flex: 1;">
                                <div class="item-label">工序</div>
                                <div><span class="badge">{row['製造工序']}</span></div>
                            </div>
                            <div class="list-item">
                                <div class="item-label">主要人員</div>
                                <div class="item-value">👤 {row['作業人員']}</div>
                            </div>
                            <div class="list-item">
                                <div class="item-label">協助人員</div>
                                <div class="item-value">🤝 {row.get('協助人員', '無')}</div>
                            </div>
                            <div class="list-item">
                                <div class="item-label">派工日期</div>
                                <div class="item-value date-text">📅 {row['作業期限']}</div>
                            </div>
                            <div class="list-item">
                                <div class="item-label">派工人員</div>
                                <div class="item-value">🚩 {row['派工人員']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- 修改部分：按鈕並排 ---
                        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 4])
                        with btn_c1:
                            if st.button(f"✅ 完工 (製令:{row['製令']})", key=f"done_{row['db_key']}"):
                                done_data = row.to_dict()
                                db_key = done_data.pop('db_key')
                                done_data['實際完工時間'] = get_now_str()
                                requests.post(f"{DONE_URL}.json", json=done_data)
                                requests.delete(f"{DB_URL}/{db_key}.json")
                                st.balloons()
                                st.rerun()
                        
                        with btn_c2:
                            if st.button(f"📝 編輯 (製令:{row['製令']})", key=f"edit_{row['db_key']}"):
                                # 點擊後跳轉到編輯頁面並記錄選中的 ID
                                st.session_state.target_edit_id = row['db_key']
                                # 切換導航選單 (透過 st.sidebar 邏輯或是直接跳轉)
                                # 這裡直接讓用戶知道去「編輯派工紀錄」選單
                                st.info(f"請點擊左側「📝 編輯派工紀錄」來修改此筆資料。")

            else:
                st.info("目前尚無待辦派工。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. ✅ 已完工歷史紀錄查詢 ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                df_done = pd.DataFrame(list(done_data.values())).fillna("無")
                if "作業期限" in df_done.columns:
                    df_done = df_done.rename(columns={"作業期限": "派工日期"})
                st.dataframe(df_done, use_container_width=True, hide_index=True)
        except: st.error("無紀錄")

    # --- 5. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.markdown('<p class="main-title">📝 建立新派工任務</p>', unsafe_allow_html=True)
        
        order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
        process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
        
        c1, c2, c3 = st.columns(3)
        assigner_list = settings.get("assigners", [])
        assigner = c1.selectbox("🚩 派工人員", assigner_list, index=assigner_list.index(st.session_state.user) if st.session_state.user in assigner_list else 0)
        
        my_workers = settings.get("worker_map", {}).get(assigner, [])
        worker = c2.selectbox("👷 主要人員", my_workers)
        assistant = c3.selectbox("🤝 協助人員", ["無"] + my_workers)
        deadline = st.date_input("📅 派工日期", datetime.date.today() + datetime.timedelta(days=1))
        
        if st.button("🚀 發布任務"):
            if not worker: st.error("該派工人員尚未配置作業人員。")
            else:
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.balloons() 
                st.success(f"任務 [{order_no}] 已成功發布！")

    # --- 6. 📝 編輯派工紀錄 ---
    elif menu == "📝 編輯派工紀錄":
        st.markdown('<p class="main-title">📝 待辦紀錄編輯維護</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                logs = [{"id": k, **v} for k, v in db_data.items() if v]
                log_opts = {l['id']: f"{l['製令']} - {l['作業人員']}" for l in logs}
                
                # 若從首頁過來，自動帶入選取的 ID
                default_idx = 0
                if "target_edit_id" in st.session_state and st.session_state.target_edit_id in log_opts:
                    default_idx = list(log_opts.keys()).index(st.session_state.target_edit_id)
                
                target_id = st.selectbox("選擇紀錄", options=list(log_opts.keys()), index=default_idx, format_func=lambda x: log_opts[x])
                curr = next(l for l in logs if l['id'] == target_id)
                
                with st.form("edit_form"):
                    e_order = st.selectbox("修改製令編號", settings.get("orders", []), index=settings.get("orders", []).index(curr['製令']) if curr['製令'] in settings.get("orders", []) else 0)
                    e_assigner = st.selectbox("修改派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(curr['派工人員']) if curr['派工人員'] in settings.get("assigners", []) else 0)
                    e_worker_list = settings.get("worker_map", {}).get(e_assigner, [])
                    e_worker = st.selectbox("修改作業人員", e_worker_list, index=e_worker_list.index(curr['作業人員']) if curr['作業人員'] in e_worker_list else 0)
                    
                    if st.form_submit_button("💾 儲存修改"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": e_order, "派工人員": e_assigner, "作業人員": e_worker})
                        st.success("修改成功")
                        if "target_edit_id" in st.session_state: del st.session_state.target_edit_id
                        st.rerun()
                if st.button("🗑️ 刪除任務", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json"); st.rerun()
            else: st.info("無待辦紀錄。")
        except: st.error("讀取失敗")

    # --- 7. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.markdown('<p class="main-title">⚙️ 系統內容管理</p>', unsafe_allow_html=True)
        with st.form("sys_config"):
            n_orders = st.text_area("📦 製令清單", value=",".join(settings.get("orders", [])), height=100)
            n_assigners = st.text_area("🚩 派工人員清單", value=",".join(settings.get("assigners", [])), height=100)
            n_processes = st.text_area("⚙️ 製造工序清單", value=",".join(settings.get("processes", [])), height=100)
            if st.form_submit_button("儲存系統清單"):
                settings["orders"] = [x.strip() for x in n_orders.split(",") if x.strip()]
                settings["assigners"] = [x.strip() for x in n_assigners.split(",") if x.strip()]
                settings["processes"] = [x.strip() for x in n_processes.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json=settings)
                st.rerun()
