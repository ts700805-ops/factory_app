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
        if "processes" not in data or not data["processes"]:
            data["processes"] = ["預設工序"]
        if "worker_map" not in data:
            data["worker_map"] = {}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["工序A", "工序B"]}

# --- 2. 頁面樣式設計 (維持您喜歡的風格) ---
st.set_page_config(page_title="超慧科技●現場派工看板", layout="wide")

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
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    if st.button("確認進入系統"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
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
                proc_list = settings.get("processes", [])
                for k, v in data.items():
                    if not v: continue
                    
                    st.markdown(f"""
                    <div class="order-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="order-id">📦 製令單：{v.get('製令', '未知')}</span>
                            <span style="color: #64748b;">🚩 派工員：{v.get('派工人員','-')} | ⏳ 期限：{v.get('作業期限','-')}</span>
                        </div>
                        <table class="proc-table">
                            <tr>
                                {" ".join([f"<th>{p}</th>" for p in proc_list])}
                            </tr>
                            <tr>
                                {" ".join([f'<td class="{"worker-active" if v.get(p, "NA") != "NA" else "worker-na"}">{v.get(p, "NA")}</td>' for p in proc_list])}
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"✅ 製令 {v.get('製令')} 全工序完工報工", key=f"fin_{k}", use_container_width=True):
                        done_data = v.copy()
                        done_data['實際完工時間'] = get_now_str()
                        requests.post(f"{DONE_URL}.json", data=json.dumps(done_data, ensure_ascii=False).encode('utf-8'))
                        requests.delete(f"{DB_URL}/{k}.json")
                        st.balloons()
                        st.rerun()
            else:
                st.info("目前尚無派工任務。")
        except Exception as e:
            st.error(f"連線錯誤：{e}")

    # --- 4. 💖 愛的派工作業中心 (修正錯誤處) ---
    elif menu == "💖 愛的派工作業中心":
        st.markdown('<p class="main-title">💖 愛的派工作業中心</p>', unsafe_allow_html=True)
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            order_input = c1.text_input("1. 輸入製令編號", placeholder="例如: 25M0677-01")
            assign_list = settings.get("assigners", [])
            selected_assigner = c2.selectbox("2. 確認派工人員", assign_list, index=assign_list.index(st.session_state.user) if st.session_state.user in assign_list else 0)
            
            st.markdown("### 3. 指派各工序負責人")
            
            workers = ["NA"] + settings.get("worker_map", {}).get(selected_assigner, [])
            proc_list = settings.get("processes", [])
            
            new_assign_data = {}
            cols_per_row = 4
            for i in range(0, len(proc_list), cols_per_row):
                row_procs = proc_list[i:i+cols_per_row]
                cols = st.columns(cols_per_row)
                for j, p_name in enumerate(row_procs):
                    with cols[j]:
                        new_assign_data[p_name] = st.selectbox(p_name, workers, key=f"sel_{p_name}")
            
            st.markdown("---")
            deadline = st.date_input("4. 設定預計完工期限", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.button("🚀 確認發布此製令單至看板", type="primary", use_container_width=True):
                if not order_input:
                    st.error("❌ 請務必填寫『製令編號』！")
                elif not proc_list:
                    st.error("❌ 尚未定義工序，請至系統管理設定。")
                else:
                    # 修正：確保日期與所有資料轉換為字串格式
                    payload = {
                        "製令": str(order_input),
                        "派工人員": str(selected_assigner),
                        "作業期限": deadline.strftime("%Y-%m-%d"), # 修正：日期物件不可直接發送
                        "提交時間": get_now_str(),
                        **{str(k): str(v) for k, v in new_assign_data.items()} # 確保 Key/Value 皆為字串
                    }
                    try:
                        # 修正：使用 json.dumps 確保 JSON 格式正確
                        res = requests.post(
                            f"{DB_URL}.json", 
                            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                            timeout=10
                        )
                        if res.status_code == 200:
                            st.success(f"✅ 製令 {order_input} 派工完成！")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"發送失敗，代碼：{res.status_code}，訊息：{res.text}")
                    except Exception as e:
                        st.error(f"系統連線錯誤：{e}")

    # --- 5. 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.markdown('<p class="main-title">⚙️ 系統內容管理</p>', unsafe_allow_html=True)
        with st.form("basic_settings"):
            st.subheader("🛠️ 基本名單編輯")
            new_assigners = st.text_area("🚩 編輯派工人員 (用英文逗點隔開)", value=",".join(settings.get("assigners", [])))
            new_processes = st.text_area("⚙️ 編輯工序清單 (用英文逗點隔開)", value=",".join(settings.get("processes", [])))
            if st.form_submit_button("💾 儲存名單定義"):
                update_payload = {
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.patch(f"{SETTING_URL}.json", data=json.dumps(update_payload, ensure_ascii=False).encode('utf-8'))
                st.success("名單已更新！")
                st.rerun()

        st.markdown("---")
        target_assigner = st.selectbox("請選擇派工人員來配置所屬作業員：", settings.get("assigners", []))
        if target_assigner:
            with st.form("worker_config"):
                worker_input = st.text_area(f"👷 {target_assigner} 的作業員清單 (用英文逗點隔開)", value=",".join(settings.get("worker_map", {}).get(target_assigner, [])))
                if st.form_submit_button("💾 儲存人員配置"):
                    wm = settings.get("worker_map", {})
                    wm[target_assigner] = [x.strip() for x in worker_input.split(",") if x.strip()]
                    requests.patch(f"{SETTING_URL}.json", data=json.dumps({"worker_map": wm}, ensure_ascii=False).encode('utf-8'))
                    st.success(f"{target_assigner} 的名單已更新！")
                    st.rerun()

    # --- 6. 完工紀錄 ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_json = r_done.json()
            if done_json:
                df_done = pd.DataFrame([v for k, v in done_json.items() if v]).fillna("NA")
                st.dataframe(df_done, use_container_width=True)
            else:
                st.info("尚無歷史紀錄。")
        except:
            st.error("讀取歷史紀錄失敗。")
