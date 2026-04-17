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

# --- 2. 頁面樣式設計 (嚴格保留原風格) ---
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
                        requests.post(f"{DONE_URL}.json", json=done_data)
                        requests.delete(f"{DB_URL}/{k}.json")
                        st.rerun()
            else:
                st.info("目前無待辦任務。")
        except Exception as e:
            st.error(f"連線異常：{e}")

    # --- 4. 💖 愛的派工作業中心 (修正重點區域) ---
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
            deadline = st.date_input("4. 設定作業期限", datetime.date.today())
            
            if st.button("🚀 確認發布此製令單至看板", type="primary", use_container_width=True):
                if order_input:
                    # 【核心修正】：手動格式化所有可能導致 JSON 解析失敗的欄位
                    try:
                        final_payload = {
                            "製令": str(order_input),
                            "派工人員": str(selected_assigner),
                            "作業期限": deadline.strftime("%Y-%m-%d"), # 強制轉為字串
                            "提交時間": get_now_str()
                        }
                        # 合併工序資料並確保皆為字串
                        for pk, pv in new_assign_data.items():
                            final_payload[str(pk)] = str(pv)
                        
                        # 【雙重保險】：直接發送 json 參數，由 requests 自動處理 header 與序列化
                        res = requests.post(f"{DB_URL}.json", json=final_payload, timeout=10)
                        
                        if res.status_code == 200:
                            st.success("✅ 派工成功！")
                            st.rerun()
                        else:
                            # 顯示更細節的錯誤以利除錯
                            st.error(f"發送失敗 ({res.status_code}): {res.text}")
                    except Exception as ex:
                        st.error(f"系統錯誤: {ex}")
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
                requests.patch(f"{SETTING_URL}.json", json=payload)
                st.rerun()

    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄</p>', unsafe_allow_html=True)
        r_done = requests.get(f"{DONE_URL}.json")
        if r_done.json():
            st.dataframe(pd.DataFrame(list(r_done.json().values())), use_container_width=True)
