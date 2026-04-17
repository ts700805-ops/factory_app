import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 ---
# 確保您的 Firebase Database 規則已設定為讀寫無需授權 (auth == null)
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    """從資料庫抓取人員與工序清單，加強防錯機制確保選單不消失"""
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                # 確保抓取的資料不是空的且包含必要鍵值
                staff = data.get("all_staff", default_settings["all_staff"])
                procs = data.get("processes", default_settings["processes"])
                return {"all_staff": staff, "processes": procs}
        return default_settings
    except Exception:
        return default_settings

# --- 2. 頁面配置 ---
st.set_page_config(page_title="大量科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 20px; }
    .order-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-top: 10px solid #1E3A8A;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .order-title { font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 15px; }
    .process-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
    }
    .process-box {
        background: #f8fafc;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .process-name { font-size: 14px; color: #64748b; margin-bottom: 5px; }
    .worker-name { font-size: 16px; font-weight: bold; color: #1e40af; }
    .na-tag { color: #cbd5e1; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# 初始讀取設定
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]

# 登入機制
if "user" not in st.session_state:
    st.title("⚓ 製造部控制塔台 - 登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("啟航登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁進度)", "📝 愛的派工中心", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 ---
    if menu == "📊 控制塔台 (首頁進度)":
        st.markdown('<p class="main-title">📊 大量科技●控制塔台看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v and isinstance(v, dict)]
                if all_logs:
                    df = pd.DataFrame(all_logs)
                    unique_orders = df["製令"].unique()
                    
                    for order in unique_orders:
                        order_df = df[df["製令"] == order]
                        st.markdown(f'''
                        <div class="order-container">
                            <div class="order-title">📦 製令單：{order}</div>
                            <div class="process-grid">
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            matched = order_df[order_df["製造工序"] == proc]
                            if not matched.empty:
                                worker_display = matched.iloc[0].get("人員1", "未知")
                                html_worker = f'<span class="worker-name">{worker_display}</span>'
                            else:
                                html_worker = '<span class="na-tag">NA</span>'
                            
                            st.markdown(f'''
                                <div class="process-box">
                                    <div class="process-name">{proc}</div>
                                    {html_worker}
                                </div>
                            ''', unsafe_allow_html=True)
                        st.markdown('</div></div>', unsafe_allow_html=True)
                else:
                    st.info("目前無有效派工紀錄。")
            else:
                st.info("目前無任何派工紀錄。")
        except Exception as e:
            st.error(f"資料讀取失敗，請檢查網路連線。")

    # --- 4. 📝 愛的派工中心 (修正下拉選單) ---
    elif menu == "📝 愛的派工中心":
        st.markdown('<p class="main-title">📝 愛的派工中心 (新任務)</p>', unsafe_allow_html=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.text_input("📦 輸入製令編號", placeholder="例如: 1111")
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.markdown("---")
            st.subheader("👥 主要人員與派工人員配置 (共5位)")
            pc1, pc2, pc3, pc4, pc5 = st.columns(5)
            w1 = pc1.selectbox("人員 1 (主)", all_staff, key="nw1")
            w2 = pc2.selectbox("人員 2", all_staff, key="nw2")
            w3 = pc3.selectbox("人員 3", all_staff, key="nw3")
            w4 = pc4.selectbox("人員 4", all_staff, key="nw4")
            w5 = pc5.selectbox("人員 5", all_staff, key="nw5")
            
            user_idx = all_staff.index(st.session_state.user) if st.session_state.user in all_staff else 0
            assigner = st.selectbox("🚩 指定派工人員", all_staff, index=user_idx)
            
            if st.form_submit_button("🚀 發布任務"):
                if not order_no:
                    st.error("請輸入製令編號！")
                else:
                    log = {
                        "製令": order_no,
                        "製造工序": proc_name,
                        "人員1": w1, "人員2": w2, "人員3": w3, "人員4": w4, "人員5": w5,
                        "派工人員": assigner,
                        "提交時間": get_now_str()
                    }
                    try:
                        # 修正：確保路徑正確且使用 json.dumps 確保格式
                        resp = requests.post(f"{DB_URL}.json", data=json.dumps(log), timeout=5)
                        if resp.status_code == 200:
                            st.success(f"製令 {order_no} 已同步至控制塔台！")
                            st.balloons()
                        else:
                            st.error(f"發送失敗，代碼：{resp.status_code}，訊息：{resp.text}")
                    except Exception as e:
                        st.error(f"發送失敗：{str(e)}")

    # --- 5. 📝 編輯派工紀錄 ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 派工紀錄管理")
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                log_options = {log['id']: f"[{log.get('製令', '無')}] {log.get('製造工序', '無')} - {log.get('人員1', '無')}" for log in all_logs}
                
                target_id = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                
                if curr:
                    with st.expander("📝 編輯內容", expanded=True):
                        def get_idx(val, lst):
                            return lst.index(val) if val in lst else 0

                        edit_proc = st.selectbox("修改工序", process_list, index=get_idx(curr.get('製造工序'), process_list))
                        
                        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                        nw1 = ec1.selectbox("人員1", all_staff, index=get_idx(curr.get('人員1'), all_staff), key="e1")
                        nw2 = ec2.selectbox("人員2", all_staff, index=get_idx(curr.get('人員2'), all_staff), key="e2")
                        nw3 = ec3.selectbox("人員3", all_staff, index=get_idx(curr.get('人員3'), all_staff), key="e3")
                        nw4 = ec4.selectbox("人員4", all_staff, index=get_idx(curr.get('人員4'), all_staff), key="e4")
                        nw5 = ec5.selectbox("人員5", all_staff, index=get_idx(curr.get('人員5'), all_staff), key="e5")
                        
                        if st.button("💾 儲存修改"):
                            update_data = {
                                "製造工序": edit_proc,
                                "人員1": nw1, "人員2": nw2, "人員3": nw3, "人員4": nw4, "人員5": nw5
                            }
                            requests.patch(f"{DB_URL}/{target_id}.json", data=json.dumps(update_data))
                            st.success("已更新！")
                            st.rerun()
                    
                    if st.button("🗑️ 刪除此筆紀錄", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
            else:
                st.info("無待辦紀錄。")
        except:
            st.error("讀取錯誤")

    # --- 6. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統名單設定")
        with st.form("sys_config"):
            st.info("💡 修改後請點擊儲存，這將更新所有下拉選單的內容。")
            all_staff_str = st.text_area("👥 人員名單 (逗號分隔)", value=",".join(all_staff))
            new_processes = st.text_area("⚙️ 工序清單 (逗號分隔)", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並重置選單"):
                new_data = {
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                try:
                    # 使用 put 覆蓋舊設定，確保結構完整
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data), timeout=5)
                    st.success("系統設定已更新！")
                    st.rerun()
                except:
                    st.error("儲存失敗，請檢查資料庫連線。")
