import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math

# --- 1. 核心資料與設定 --- (維持不變)
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs" 
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "人員C"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01", "12345"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 --- (針對 3 欄做微調)
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card { background: white; border-radius: 8px; border: 2px solid #1e40af; margin-bottom: 20px; overflow: hidden; }
    .order-title { background: #1e40af; color: white; padding: 10px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; }
    .power-date { background: #fbbf24; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 13px; white-space: nowrap; }
    
    .table-row { 
        display: flex; 
        border-bottom: 1px solid #dee2e6; 
        min-height: 52px; 
        align-items: stretch; 
        width: 100%;
    }
    .cell-proc { 
        width: 85px; 
        min-width: 85px; 
        background: #f1f5f9; 
        color: #1e40af; 
        font-weight: 800; 
        padding: 8px; 
        border-right: 1px solid #dee2e6;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        text-align: center;
    }
    .cell-staff { 
        flex-grow: 1; 
        padding: 6px; 
        display: flex; 
        flex-wrap: wrap; 
        gap: 4px; 
        align-items: center;
        background: white;
    }
    
    .badge-leader { background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-main { background: #1e40af; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; border: 1px solid #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 --- (維持不變)
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄")
    u = st.selectbox("👤 請選擇您的姓名", sorted(list(set(all_leaders + all_staff))))
    if st.button("確認進入", use_container_width=True):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **{st.session_state.user}**，您好")
    menu = st.sidebar.radio("功能選單", ["📊 製造部公佈欄", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部公佈欄 (改為一橫列顯示 3 個製令) ---
    if menu == "📊 製造部公佈欄":
        st.markdown('<h2 style="text-align:center; color:#1e40af;">📋 派工進度</h2>', unsafe_allow_html=True)
        
        with st.expander("🔍 搜尋篩選"):
            s_order = st.selectbox("製令", ["全部"] + sorted(order_list))
            s_staff = st.selectbox("人員", ["全部"] + sorted(list(set(all_leaders + all_staff))))

        try:
            r = requests.get(f"{DB_URL}.json", timeout=10)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs).fillna("NA")
                
                unique_orders = df["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or str(o) == str(s_order))]
                
                if s_staff != "全部":
                    check_cols = ["組長", "人員1", "人員2", "人員3", "人員4", "人員5"]
                    filtered_orders = [o for o in filtered_orders if df[df["製令"]==o][check_cols].apply(lambda x: s_staff in x.values, axis=1).any()]

                # 重點：建立 3 欄容器
                main_cols = st.columns(3)
                
                for i, o_id in enumerate(filtered_orders):
                    o_df = df[df["製令"] == o_id]
                    p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    
                    # 依據索引餘數決定放在哪一欄
                    with main_cols[i % 3]:
                        st.markdown(f'''
                            <div class="order-card">
                                <div class="order-title">
                                    <span>📦 {o_id}</span>
                                    <span class="power-date">⚡ {p_date}</span>
                                </div>
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            # 在每一欄內的卡片裡，[內容] 佔大比例，[按鈕] 佔小比例
                            row_cols = st.columns([0.82, 0.18])
                            
                            if not match.empty:
                                row = match.iloc[0]
                                staff_html = f'<div class="badge-leader">L: {row.get("組長","")}</div>'
                                if row.get("人員1") != "NA": staff_html += f'<div class="badge-main">{row.get("人員1")}</div>'
                                for j in range(2, 6):
                                    if row.get(f"人員{j}") not in ["NA", ""]: 
                                        staff_html += f'<div class="badge-sub">{row.get(f"人員{j}")}</div>'
                                
                                with row_cols[0]: 
                                    st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                                with row_cols[1]:
                                    st.write("") # 垂直對齊補位
                                    if st.button("✅", key=f"fin_{row['id']}", use_container_width=True):
                                        clean_data = {k: (v if not (isinstance(v, float) and math.isnan(v)) else "NA") for k, v in row.to_dict().items()}
                                        clean_data["完工時間"] = get_now_str()
                                        clean_data["完工人員"] = st.session_state.user
                                        requests.post(f"{FINISH_URL}.json", data=json.dumps(clean_data))
                                        requests.delete(f"{DB_URL}/{row['id']}.json")
                                        st.rerun()
                            else:
                                with row_cols[0]: 
                                    st.markdown(f'<div class="table-row"><div class="cell-proc" style="color:#cbd5e1;">{proc}</div><div class="cell-staff" style="color:#cbd5e1; font-size:11px;">未派工</div></div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True) # 卡片結束
            else: st.info("💡 目前無派工紀錄")
        except: st.error("❌ 資料讀取異常")

    # --- 其餘選單維持您原本的程式碼邏輯 ---
    elif menu == "📜 完工紀錄查詢":
        st.write("完工紀錄查詢模組...")
    elif menu == "📝 任務派發":
        st.write("任務派發模組...")
    elif menu == "⚙️ 設定管理":
        st.write("設定管理模組...")
