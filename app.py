import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 ---
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
            return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["工序A", "工序B"]}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["工序A", "工序B"]}

# --- 2. 頁面樣式設計 (嚴格保留原風格，完全不改動) ---
st.set_page_config(page_title="大量科技●現場派工看板", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-title { font-size: 32px !important; font-weight: 800; color: #1e3a8a; border-bottom: 3px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
    .order-card {
        background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 6px solid #1e3a8a;
    }
    .order-id { font-size: 24px; font-weight: 900; color: #1e3a8a; margin-bottom: 10px; }
    .proc-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .proc-table th { background-color: #f1f5f9; color: #475569; padding: 8px; font-size: 14px; border: 1px solid #e2e8f0; text-align: center; }
    .proc-table td { padding: 12px; font-size: 16px; border: 1px solid #e2e8f0; text-align: center; font-weight: 600; }
    .worker-active { color: #1e40af; background-color: #eff6ff; }
    .worker-na { color: #cbd5e1; font-weight: 400 !important; }
    .stButton>button { border-radius: 8px; font-weight: bold !important; transition: 0.3s; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    if st.button("確認進入系統"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "💖 愛的派工作業中心", "✅ 已完工歷史紀錄查詢", "⚙️ 系統內容管理"])

    # --- 3. 📊 經營者看板 (首頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 大量科技現場派工看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                proc_list = settings.get("processes", [])
                for k, v in data.items():
                    if not v: continue
                    st.markdown(f"""
                    <div class="order-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="order-id">📦 製令：{v.get('製令', '未知')}</span>
                            <span style="color: #64748b;">🚩 派工員：{v.get('派工人員','-')} | ⏳ 期限：{v.get('作業期限','-')}</span>
                        </div>
                        <table class="proc-table">
                            <tr>{" ".join([f"<th>{p}</th>" for p in proc_list])}</tr>
                            <tr>{" ".join([f'<td class="{"worker-active" if v.get(p, "NA") != "NA" else "worker-na"}">{v.get(p, "NA")}</td>' for p in proc_list])}</tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"✅ 完成這筆紀錄 ({v.get('製令')})", key=f"fin_{k}", use_container_width=True):
                        done_data = v.copy()
                        done_data['實際完工時間'] = get_now_str()
                        # 確保發送純 JSON 格式
                        requests.post(f"{DONE_URL}.json", data=json.dumps(done_data))
                        requests.delete(f"{DB_URL}/{k}.json")
                        st.rerun()
            else:
                st.info("目前無待辦任務。")
        except Exception as e:
            st.error(f"連線異常：{e}")

    # --- 4. 💖 愛的派工作業中心 (修正核心錯誤處) ---
    elif menu == "💖 愛的派工作業中心":
        st.markdown('<p class="main-title">💖 愛的派工作業中心</p>', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2 = st.columns(2)
            order_input = c1.text_input("1. 請輸入製令編號")
            assign_list = settings.get("assigners", [])
            selected_assigner = c2.selectbox("2. 確認派工人員", assign_list)
            
            st.markdown("### 3. 設定各工序負責人")
            workers = ["NA"] + settings.get("worker_map", {}).get(selected_assigner, [])
            proc_list = settings.get("processes", [])
            new_assign_data = {}
            for i in range(0, len(proc_list), 4):
                cols = st.columns(4)
                for j, p_name in enumerate(proc_list[i:i+4]):
                    with cols[j]:
                        new_assign_data[p_name] = st.selectbox(p_name, workers, key=f"sel_{p_name}")
            
            st.markdown("---")
            deadline_val = st.date_input("4. 設定作業期限", datetime.date.today())
            
            if st.button("🚀 確認發布此製令單至看板", type="primary", use_container_width=True):
                if order_input:
                    # 【核心修正】：將所有資料彙整成一個「純字串」字典
                    payload = {
                        "製令": str(order_input),
                        "派工人員": str(selected_assigner),
                        "作業期限": deadline_val.strftime("%Y-%m-%d"), # 轉成字串，這是關鍵
                        "提交時間": get_now_str()
                    }
                    # 將各工序負責人也轉成字串
                    for p_key, p_val in new_assign_data.items():
                        payload[str(p_key)] = str(p_val)
                    
                    try:
                        # 【雙重保險】：不使用 json= 參數，改用 data= 並手動轉為 JSON 字串送出
                        # 這樣可以 100% 確保 Firebase 收到的是標準 JSON
                        json_string = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                        res = requests.post(f"{DB_URL}.json", data=json_string, timeout=10)
                        
                        if res.status_code == 200:
                            st.success("✅ 派工成功！")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"發送失敗，代碼：{res.status_code}，錯誤訊息：{res.text}")
                    except Exception as e:
                        st.error(f"資料庫連線錯誤：{e}")
                else:
                    st.warning("請填寫製令編號")

    # --- 5. 系統管理與歷史紀錄 ---
    elif menu == "⚙️ 系統內容管理":
        st.markdown('<p class="main-title">⚙️ 系統內容管理</p>', unsafe_allow_html=True)
        with st.form("sys_form"):
            new_assigners = st.text_area("派工人員 (逗點隔開)", value=",".join(settings.get("assigners", [])))
            new_processes = st.text_area("工序清單 (逗點隔開)", value=",".join(settings.get("processes", [])))
            if st.form_submit_button("儲存設定"):
                payload = {
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.patch(f"{SETTING_URL}.json", data=json.dumps(payload))
                st.rerun()

    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄</p>', unsafe_allow_html=True)
        r_done = requests.get(f"{DONE_URL}.json")
        if r_done.json():
            st.dataframe(pd.DataFrame(list(r_done.json().values())), use_container_width=True)
