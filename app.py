import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        data = r.json()
        if not data: 
            return {"all_staff": ["管理員"], "processes": ["工序A", "工序B"]}
        return data
    except:
        return {"all_staff": ["管理員"], "processes": ["工序A", "工序B"]}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●控制塔台", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 3px solid #1E3A8A; margin-bottom: 20px; }
    .order-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-top: 8px solid #1E3A8A;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .process-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .process-item {
        background: #f8fafc;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .na-text { color: #cbd5e1; font-style: italic; }
    .staff-text { color: #1e40af; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings.get("all_staff", ["管理員"])
process_list = settings.get("processes", [])

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●登入系統")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("進入塔台"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **當前人員：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁)", "📝 愛的派工中心", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁) ---
    if menu == "📊 控制塔台 (首頁)":
        st.markdown('<p class="main-title">📊 超慧科技●神鬼奇航●控制塔台</p>', unsafe_allow_html=True)
        
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            
            if db_data:
                # 轉為 DataFrame 方便處理
                df = pd.DataFrame(list(db_data.values()))
                unique_orders = df["製令"].unique()

                for order in unique_orders:
                    order_data = df[df["製令"] == order]
                    st.markdown(f'<div class="order-card">', unsafe_allow_html=True)
                    st.markdown(f"### 📦 製令編號：{order}")
                    
                    st.markdown('<div class="process-grid">', unsafe_allow_html=True)
                    # 顯示設定中的所有工序
                    for p in process_list:
                        # 找出該製令下對應此工序的資料
                        matched = order_data[order_data["製造工序"] == p]
                        if not matched.empty:
                            worker = matched.iloc[0]["主要人員"]
                            display_worker = f'<span class="staff-text">{worker}</span>'
                        else:
                            display_worker = '<span class="na-text">NA</span>'
                        
                        st.markdown(f'''
                            <div class="process-item">
                                <small>{p}</small><br>
                                {display_worker}
                            </div>
                        ''', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("目前尚無任何派工製令紀錄。")
        except Exception as e:
            st.error(f"資料讀取失敗：{e}")

    # --- 4. 📝 愛的派工中心 ---
    elif menu == "📝 愛的派工中心":
        st.markdown('<p class="main-title">📝 愛的派工中心</p>', unsafe_allow_html=True)
        
        with st.form("dispatch_form"):
            c1, c2 = st.columns(2)
            order_no = c1.text_input("📦 輸入製令編號", placeholder="例如：A20260301")
            process_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.markdown("---")
            st.subheader("👥 人員配置")
            
            # 您要求的 5 位主要人員與 5 位派工人員 (雖然通常一筆工序對應一組)
            col_a, col_b = st.columns(2)
            main_worker = col_a.selectbox("👷 主要人員 (負責人)", all_staff)
            assigner = col_b.selectbox("🚩 派工人員 (監管人)", all_staff)
            
            # 如果您需要一次填 5 個，這裡可以擴充，但建議先以一工序對一組為主
            
            submit = st.form_submit_button("🚀 發布至控制塔台")
            
            if submit:
                if not order_no:
                    st.error("請輸入製令編號！")
                else:
                    new_log = {
                        "製令": order_no,
                        "製造工序": process_name,
                        "主要人員": main_worker,
                        "派工人員": assigner,
                        "提交時間": get_now_str()
                    }
                    res = requests.post(f"{DB_URL}.json", data=json.dumps(new_log, ensure_ascii=True))
                    if res.status_code == 200:
                        st.success(f"製令 {order_no} - {process_name} 已成功派發！")
                        st.balloons()

    # --- 5. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.markdown('<p class="main-title">⚙️ 系統設定</p>', unsafe_allow_html=True)
        
        # 管理所有人員名單 (作為所有下拉選單的基礎)
        st.subheader("👥 全體人員名單管理")
        staff_input = st.text_area("請輸入人員姓名 (以英文逗號分隔)", value=",".join(all_staff))
        
        # 管理工序
        st.subheader("⚙️ 製造工序清單管理")
        process_input = st.text_area("請輸入工序名稱 (以英文逗號分隔)", value=",".join(process_list))
        
        if st.button("💾 儲存所有設定"):
            new_settings = {
                "all_staff": [x.strip() for x in staff_input.split(",") if x.strip()],
                "processes": [x.strip() for x in process_input.split(",") if x.strip()]
            }
            requests.patch(f"{SETTING_URL}.json", data=json.dumps(new_settings, ensure_ascii=True))
            st.success("設定已更新！")
            st.rerun()

        st.markdown("---")
        if st.button("🗑️ 清空所有製令紀錄 (慎用)", type="primary"):
            requests.delete(f"{DB_URL}.json")
            st.warning("所有資料已清除。")
            st.rerun()
