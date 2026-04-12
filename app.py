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

# --- 2. 頁面配置 (修正手機版字體) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 修正手機版看板數據看不清楚的問題 */
    .stat-card { 
        background-color: #ffffff; 
        padding: 15px 5px; 
        border-radius: 10px; 
        border-top: 5px solid #1E3A8A; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        text-align: center; 
        margin-bottom: 15px; 
    }
    .stat-label { font-size: 20px !important; font-weight: bold; color: #666; }
    .stat-value { 
        font-size: 56px !important; /* 顯著放大數字，確保手機可見 */
        font-weight: bold; 
        color: #1E3A8A; 
        line-height: 1; 
        display: block;
        margin: 10px 0;
    }
    .stat-unit { font-size: 18px !important; color: #1E3A8A; }

    /* 其他介面優化 */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div { font-size: 18px !important; font-weight: bold !important; }
    .main-title { font-size: 30px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stButton>button { height: 60px; font-size: 24px !important; font-weight: bold !important; }
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
                
                # 看板區域
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card"><span class="stat-label">總派件數</span><br><span class="stat-value">{len(df)}</span><span class="stat-unit">件</span></div>', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card"><span class="stat-label">動員人力</span><br><span class="stat-value">{worker_count}</span><span class="stat-unit">人</span></div>', unsafe_allow_html=True)
                
                with st.expander("🔍 快速篩選資料", expanded=True):
                    f1, f2, f3, f4 = st.columns(4)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序篩選", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員篩選", ["全部"] + sorted(df["派工人員"].unique().tolist()))
                    sel_worker = f4.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]

                st.subheader("📑 待辦派工明細清單") 
                display_cols = ["製令", "製造工序", "派工人員", "作業人員", "協助人員", "作業期限"]
                st.dataframe(filtered_df[[c for c in display_cols if c in filtered_df.columns]], use_container_width=True, height=300, hide_index=True)

                st.markdown("---")
                st.subheader("📦 快速結案")
                for index, row in filtered_df.iterrows():
                    with st.container():
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"### 📦 製令：{row['製令']} | 👷 作業員：{row['作業人員']}")
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
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        # 此區塊邏輯保留不變...
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = [dict(v, done_key=k) for k, v in done_data.items() if v]
                df_done = pd.DataFrame(done_list).fillna("無")
                st.dataframe(df_done.sort_values(by='實際完工時間', ascending=False), use_container_width=True, height=300, hide_index=True)

    # --- 5. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form", clear_on_submit=True):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            c1, c2, c3 = st.columns(3)
            assigner = c1.selectbox("🚩 派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(st.session_state.user) if st.session_state.user in settings.get("assigners", []) else 0)
            worker = c2.selectbox("👷 主要人員", settings.get("workers", []))
            assistant = c3.selectbox("🤝 協助人員", ["無"] + settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                res = requests.post(f"{DB_URL}.json", json=log)
                if res.status_code == 200:
                    st.balloons() # 氣球特效要在
                    st.success(f"任務 [{order_no}] 已成功發布！")
                else:
                    st.error("發布失敗。")

    # --- 6. 📝 編輯派工紀錄 (確保有派工人員與製令編輯) ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 待辦派工紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"製令：{log.get('製令')} | 主要：{log.get('作業人員')}" for log in all_logs}
                target_id = st.selectbox("選擇欲修改的派工紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                if curr:
                    with st.expander("📝 編輯內容", expanded=True):
                        c1, c2 = st.columns(2)
                        # 保留並修正編輯功能：製令與派工人員
                        edit_order = c1.selectbox("修改製令編號", settings.get("orders", []), index=settings.get("orders", []).index(curr.get('製令')) if curr.get('製令') in settings.get("orders", []) else 0)
                        edit_assigner = c2.selectbox("修改派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(curr.get('派工人員')) if curr.get('派工人員') in settings.get("assigners", []) else 0)
                        
                        c3, c4 = st.columns(2)
                        new_worker = c3.selectbox("修改主要人員", settings.get("workers", []), index=settings.get("workers", []).index(curr.get('作業人員')) if curr.get('作業人員') in settings.get("workers", []) else 0)
                        new_assist = c4.selectbox("修改協助人員", ["無"] + settings.get("workers", []), index=(["無"] + settings.get("workers", [])).index(curr.get('協助人員')) if curr.get('協助人員') in (["無"] + settings.get("workers", [])) else 0)
                        
                        if st.button("💾 儲存派工修改"):
                            patch_data = {
                                "製令": edit_order,
                                "派工人員": edit_assigner,
                                "作業人員": new_worker, 
                                "協助人員": new_assist
                            }
                            requests.patch(f"{DB_URL}/{target_id}.json", json=patch_data)
                            st.success("紀錄已更新！")
                            st.rerun()
                    
                    st.markdown("---")
                    if st.button("🗑️ 刪除此筆待辦任務", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
            else: st.info("目前沒有待辦紀錄。")
        except: st.error("讀取失敗。")

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
                st.success("系統設定已儲存！")
                st.rerun()
