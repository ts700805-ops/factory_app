import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (絕對不動) ---
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
            return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["工序1", "工序2", "工序3", "工序4", "工序5"]}
        if "worker_map" not in data: data["worker_map"] = {}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["工序1", "工序2", "工序3", "工序4", "工序5"]}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 20px; }
    .task-card {
        background: white; padding: 15px; border-radius: 12px; border-left: 8px solid #1E3A8A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .process-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
    .process-item { background: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center; }
    .process-name { font-size: 14px; color: #64748b; font-weight: bold; }
    .worker-name { font-size: 16px; color: #1e293b; font-weight: bold; }
    .na-text { color: #cbd5e1; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("我愛德文★志偉愛我"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁)", "💖 愛的派工作業中心", "✅ 已完工歷史紀錄查詢", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁) ---
    if menu == "📊 控制塔台 (首頁)":
        st.markdown('<p class="main-title">📊 超慧科技現場派工看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v]
                df = pd.DataFrame(all_logs)
                
                # 取得所有工序定義
                proc_list = settings.get("processes", [])

                for index, row in df.iterrows():
                    st.markdown(f"""
                    <div class="task-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:8px;">
                            <span style="font-size:22px; font-weight:bold; color:#1e3a8a;">📦 製令：{row['製令']}</span>
                            <span style="color:#64748b; font-size:14px;">🚩 派工員：{row['派工人員']} | ⏳ 期限：{row['作業期限']}</span>
                        </div>
                        <div class="process-grid">
                    """, unsafe_allow_html=True)
                    
                    # 顯示每個工序的派工人員，沒有則顯示 NA
                    for p_name in proc_list:
                        worker = row.get(p_name, "NA")
                        worker_html = f'<span class="worker-name">{worker}</span>' if worker != "NA" else '<span class="na-text">NA</span>'
                        st.markdown(f"""
                            <div class="process-item">
                                <div class="process-name">{p_name}</div>
                                {worker_html}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    if st.button(f"✅ 整單完工 ({row['製令']})", key=f"done_{row['db_key']}", use_container_width=True):
                        done_data = row.to_dict()
                        db_key = done_data.pop('db_key')
                        done_data['實際完工時間'] = get_now_str()
                        requests.post(f"{DONE_URL}.json", json=done_data)
                        requests.delete(f"{DB_URL}/{db_key}.json")
                        st.balloons(); st.rerun()
            else:
                st.info("目前尚無派工任務。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. 💖 愛的派工作業中心 ---
    elif menu == "💖 愛的派工作業中心":
        st.markdown('<p class="main-title">💖 愛的派工作業中心</p>', unsafe_allow_html=True)
        
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            order_no = col_a.text_input("📦 輸入製令編號 (例如: PO-2024001)")
            assign_list = settings.get("assigners", [])
            assigner = col_b.selectbox("🚩 派工人員", assign_list, index=assign_list.index(st.session_state.user) if st.session_state.user in assign_list else 0)
            
            st.markdown("---")
            st.subheader("⚙️ 設定各工序負責人")
            
            # 取得該派工員名下的所有人員作為下拉選單
            worker_options = ["NA"] + settings.get("worker_map", {}).get(assigner, [])
            proc_list = settings.get("processes", [])
            
            # 動態生成工序選單 (每行 3 個)
            proc_cols = st.columns(3)
            new_task_data = {}
            for i, p_name in enumerate(proc_list):
                with proc_cols[i % 3]:
                    new_task_data[p_name] = st.selectbox(f"工序：{p_name}", worker_options, key=f"proc_{i}")
            
            st.markdown("---")
            deadline = st.date_input("⏳ 整體作業期限", datetime.date.today() + datetime.timedelta(days=3))
            
            if st.button("🚀 確認發布此製令單", use_container_width=True, type="primary"):
                if not order_no:
                    st.error("請輸入製令編號！")
                else:
                    payload = {
                        "製令": order_no,
                        "派工人員": assigner,
                        "作業期限": str(deadline),
                        "提交時間": get_now_str(),
                        **new_task_data
                    }
                    res = requests.post(f"{DB_URL}.json", json=payload)
                    if res.status_code == 200:
                        st.success(f"製令 {order_no} 已成功發布！")
                        st.balloons()

    # --- 5. 其他功能 (歷史與管理) ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        r_done = requests.get(f"{DONE_URL}.json")
        done_data = r_done.json()
        if done_data:
            df_done = pd.DataFrame([v for k, v in done_data.items() if v]).fillna("NA")
            st.dataframe(df_done, use_container_width=True)
        else:
            st.info("尚無歷史紀錄。")

    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統內容定義")
        with st.form("sys_config"):
            new_assigners = st.text_area("🚩 編輯派工人員 (逗點隔開)", value=",".join(settings.get("assigners", [])))
            new_processes = st.text_area("⚙️ 編輯工序清單 (五位或更多，逗點隔開)", value=",".join(settings.get("processes", [])))
            if st.form_submit_button("💾 儲存基本定義"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                })
                st.rerun()
        
        st.markdown("---")
        target_assigner = st.selectbox("請選擇派工人員配置作業員：", settings.get("assigners", []))
        with st.form("worker_config"):
            worker_input = st.text_area(f"👷 {target_assigner} 的名下作業員 (逗點隔開)", value=",".join(settings.get("worker_map", {}).get(target_assigner, [])))
            if st.form_submit_button("💾 儲存人員配置"):
                wm = settings.get("worker_map", {})
                wm[target_assigner] = [x.strip() for x in worker_input.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"worker_map": wm})
                st.rerun()
