import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 配置與核心功能 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        return r.json() or {"assigners": ["陳德文"], "processes": ["配電作業", "前置作業"], "worker_map": {}}
    except:
        return {"assigners": ["陳德文"], "processes": ["配電作業", "前置作業"], "worker_map": {}}

# --- 2. 介面樣式設計 ---
st.set_page_config(page_title="超慧科技看板", layout="wide")

st.markdown("""
    <style>
    /* 全局背景與字體 */
    .stApp { background-color: #f4f7f9; }
    
    /* 製令卡片樣式：緊湊且精緻 */
    .mission-card {
        background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #edf2f7; padding-bottom: 8px; margin-bottom: 10px; }
    .card-title { font-size: 20px; font-weight: 800; color: #1e3a8a; }
    .card-process { background: #e0e7ff; color: #4338ca; padding: 2px 10px; border-radius: 6px; font-weight: bold; }
    
    /* 人員資訊區：橫向排列 */
    .staff-row { display: flex; gap: 20px; align-items: center; }
    .staff-item { display: flex; align-items: center; gap: 8px; }
    .icon-box { font-size: 18px; }
    .staff-label { color: #64748b; font-size: 14px; }
    .staff-name { font-size: 16px; font-weight: 700; color: #0f172a; }
    
    /* 下方資訊欄 */
    .info-footer { margin-top: 10px; font-size: 13px; color: #94a3b8; display: flex; justify-content: space-between; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

# --- 3. 側邊導航 ---
if "user" not in st.session_state:
    st.session_state.user = "陳德文"  # 預設登入

st.sidebar.title(f"👤 使用者：{st.session_state.user}")
menu = st.sidebar.radio("選單", ["📊 經營者看板 (首頁)", "🚀 愛的派工作業中心", "⚙️ 系統內容管理"])

# --- 4. 🚀 派工作業中心 (介面優化與錯誤修正) ---
if menu == "🚀 愛的派工作業中心":
    st.subheader("📦 新增派工任務")
    
    with st.form("dispatch_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        order_no = col1.text_input("1. 製令編號", placeholder="例如：25M0677-01")
        proc_type = col2.selectbox("2. 製造工序", settings['processes'])
        
        st.markdown("---")
        st.markdown("#### 👥 人員配置")
        c3, c4 = st.columns(2)
        all_workers = ["無"] + settings.get('worker_map', {}).get(st.session_state.user, [])
        main_worker = c3.selectbox("主手人員", all_workers)
        sub_worker = c4.selectbox("協助人員", all_workers)
        
        deadline = st.date_input("作業期限", datetime.date.today() + datetime.timedelta(days=1))
        
        submit = st.form_submit_button("🚀 確認發布至看板", use_container_width=True)
        
        if submit:
            if not order_no:
                st.error("請輸入製令編號")
            else:
                # 構建資料，確保不包含導致 400 錯誤的特殊對象
                payload = {
                    "製令": str(order_no),
                    "工序": str(proc_type),
                    "主手": str(main_worker),
                    "協助": str(sub_worker),
                    "期限": str(deadline),
                    "派工員": st.session_state.user,
                    "提交時間": get_now_str()
                }
                try:
                    res = requests.post(f"{DB_URL}.json", json=payload)
                    if res.status_code == 200:
                        st.success("✅ 發布成功！")
                        st.balloons()
                    else:
                        st.error(f"發送失敗，代碼：{res.status_code}，訊息：{res.text}")
                except Exception as e:
                    st.error(f"連線錯誤：{e}")

# --- 5. 📊 經營者看板 (緊湊型視覺展現) ---
elif menu == "📊 經營者看板 (首頁)":
    st.title("📊 生產派工即時看板")
    
    try:
        data = requests.get(f"{DB_URL}.json").json()
        if data:
            for k, v in data.items():
                if not v: continue
                # 渲染卡片
                st.markdown(f"""
                <div class="mission-card">
                    <div class="card-header">
                        <div class="card-title">📦 製令：{v.get('製令', '未知')}</div>
                        <div class="card-process">{v.get('工序', '未設定')}</div>
                    </div>
                    <div class="staff-row">
                        <div class="staff-item">
                            <span class="icon-box">👨‍🔧</span>
                            <div>
                                <div class="staff-label">主手人員</div>
                                <div class="staff-name">{v.get('主手', '無')}</div>
                            </div>
                        </div>
                        <div style="width: 2px; height: 30px; background: #e2e8f0;"></div>
                        <div class="staff-item">
                            <span class="icon-box">🤝</span>
                            <div>
                                <div class="staff-label">協助人員</div>
                                <div class="staff-name">{v.get('協助', '無')}</div>
                            </div>
                        </div>
                    </div>
                    <div class="info-footer">
                        <span>⏳ 期限：{v.get('期限', '-')}</span>
                        <span>🚩 派工：{v.get('派工員', '-')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 完工按鈕放在卡片外面
                if st.button(f"✅ 完成紀錄 ({v.get('製令')})", key=k):
                    requests.delete(f"{DB_URL}/{k}.json")
                    st.rerun()
        else:
            st.info("目前無待辦任務")
    except:
        st.error("無法取得資料，請檢查網路連線")

# --- 6. 系統設定 (略，保持原有邏輯) ---
elif menu == "⚙️ 系統內容管理":
    st.write("設定頁面已準備就緒。")
