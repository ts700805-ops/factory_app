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

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] > div { font-size: 20px !important; font-weight: bold !important; }
    div[data-testid="stDataFrame"] div[role="columnheader"] span { font-size: 22px !important; font-weight: bold !important; }
    .stSelectbox label { font-size: 26px !important; font-weight: bold !important; }
    .main-title { font-size: 36px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 5px 2px; border-radius: 10px; border-top: 4px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; font-size: 16px !important; margin-bottom: 5px; }
    .stat-value { font-size: 32px !important; font-weight: bold; color: #1E3A8A; line-height: 1.2; }
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
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span class="stat-value">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span class="stat-value">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
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
                st.subheader("📦 快速結案 (點擊按鈕標記完工)")
                for index, row in filtered_df.iterrows():
                    with st.container():
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"### 📦 製令：{row['製令']} | 👷 作業員：{row['作業人員']} | 🤝 協助：{row.get('協助人員', '無')}")
                            st.caption(f"工序：{row['製造工序']} | 期限：{row['作業期限']} | 派工：{row['派工人員']}")
                        if col_btn.button(f"✅ 完工", key=f"btn_{row['db_key']}"):
                            done_data = row.to_dict()
                            db_key = done_data.pop('db_key')
                            done_data['實際完工時間'] = get_now_str()
                            final_data = {k: (v if pd.notna(v) else "無") for k, v in done_data.items()}
                            requests.post(f"{DONE_URL}.json", json=final_data)
                            requests.delete(f"{DB_URL}/{db_key}.json")
                            st.rerun()
            else:
                st.info("目前尚無待辦派工。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. ✅ 已完工歷史紀錄查詢 (新增編輯功能) ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = []
                for k, v in done_data.items():
                    if v:
                        v['done_key'] = k
                        done_list.append(v)
                if done_list:
                    df_done = pd.DataFrame(done_list).fillna("無")
                    if '實際完工時間' in df_done.columns:
                        df_done = df_done.sort_values(by='實際完工時間', ascending=False)
                    
                    hist_display_cols = ["實際完工時間", "製令", "製造工序", "作業人員", "協助人員"]
                    st.dataframe(df_done[[c for c in hist_display_cols if c in df_done.columns]], use_container_width=True, height=300, hide_index=True)
                    
                    st.markdown("---")
                    st.subheader("🛠️ 歷史紀錄管理 (編輯 / 刪除)")
                    # 下拉選單選擇要處理的完工紀錄
                    hist_options = {row['done_key']: f"[{row.get('實際完工時間', '無')}] {row['製令']} - {row['作業人員']}" for _, row in df_done.iterrows()}
                    target_done_key = st.selectbox("請選擇要編輯或刪除的完工紀錄", options=list(hist_options.keys()), format_func=lambda x: hist_options[x])
                    
                    curr_done = next((item for item in done_list if item["done_key"] == target_done_key), None)
                    if curr_done:
                        with st.expander("📝 編輯完工資訊"):
                            ec1, ec2 = st.columns(2)
                            h_worker = ec1.selectbox("修改主要人員", settings.get("workers", []), index=settings.get("workers", []).index(curr_done.get('作業人員')) if curr_done.get('作業人員') in settings.get("workers", []) else 0)
                            worker_list_with_none = ["無"] + settings.get("workers", [])
                            h_assistant = ec2.selectbox("修改協助人員", worker_list_with_none, index=worker_list_with_none.index(curr_done.get('協助人員')) if curr_done.get('協助人員') in worker_list_with_none else 0)
                            
                            if st.button("💾 儲存歷史修改"):
                                requests.patch(f"{DONE_URL}/{target_done_key}.json", json={"作業人員": h_worker, "協助人員": h_assistant})
                                st.success("歷史紀錄已更新！")
                                st.rerun()

                        if st.button("🗑️ 刪除此筆歷史紀錄", type="primary"):
                            del_pass = st.text_input("輸入管理密碼以刪除", type="password", key="hist_del_pwd")
                            if del_pass == "1234":
                                requests.delete(f"{DONE_URL}/{target_done_key}.json")
                                st.warning("紀錄已刪除。")
                                st.rerun()
                            elif del_pass: st.error("密碼錯誤！")
                else: st.info("目前尚無完工紀錄。")
            else: st.info("目前尚無完工紀錄。")
        except Exception as e: st.error(f"讀取完工紀錄失敗：{e}")

    # --- 5. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            c1, c2, c3 = st.columns(3)
            assigner = c1.selectbox("🚩 派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(st.session_state.user) if st.session_state.user in settings.get("assigners", []) else 0)
            worker = c2.selectbox("👷 主要人員", settings.get("workers", []))
            assistant = c3.selectbox("🤝 協助人員", ["無"] + settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已發布！")
                st.rerun()

    # --- 6. 📝 編輯派工紀錄 ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 待辦派工紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = []
                for k, v in db_data.items():
                    if v: v['id'] = k; all_logs.append(v)
                if all_logs:
                    log_options = {log['id']: f"製令：{log.get('製令')} | 主要：{log.get('作業人員')}" for log in all_logs}
                    target_id = st.selectbox("選擇紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                    curr = next((i for i in all_logs if i["id"] == target_id), None)
                    if curr:
                        with st.expander("📝 編輯內容", expanded=True):
                            ec1, ec2, ec3 = st.columns(3)
                            new_worker = ec1.selectbox("主要人員", settings.get("workers", []), index=settings.get("workers", []).index(curr.get('作業人員')) if curr.get('作業人員') in settings.get("workers", []) else 0)
                            new_assist = ec2.selectbox("協助人員", ["無"] + settings.get("workers", []), index=(["無"] + settings.get("workers", [])).index(curr.get('協助人員')) if curr.get('協助人員') in (["無"] + settings.get("workers", [])) else 0)
                            if st.button("💾 儲存修改"):
                                requests.patch(f"{DB_URL}/{target_id}.json", json={"作業人員": new_worker, "協助人員": new_assist})
                                st.success("紀錄已更新！")
                                st.rerun()
                        if st.button("🗑️ 刪除紀錄", type="primary"):
                            requests.delete(f"{DB_URL}/{target_id}.json")
                            st.rerun()
            else: st.info("目前沒有待辦紀錄。")
        except: st.error("讀取資料失敗。")

    # --- 7. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            new_orders = st.text_area("📦 編輯製令清單 (逗號隔開)", value=",".join(settings.get("orders", [])), height=120)
            new_workers = st.text_area("👷 編輯人員清單", value=",".join(settings.get("workers", [])), height=100)
            if st.form_submit_button("✅ 儲存設定"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "workers": [x.strip() for x in new_workers.split(",") if x.strip()]
                })
                st.rerun()
