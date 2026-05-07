import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="獨立工時計時系統", layout="wide")

# 專業美化 CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .timer-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 15px;
        border-left: 6px solid #0052cc;
    }
    .timer-display {
        font-family: 'Courier New', monospace; font-size: 2rem; 
        color: #d32f2f; font-weight: 900;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State (確保資料存在此頁面中) ---
if 'my_tasks' not in st.session_state:
    st.session_state.my_tasks = {} # 存放正在計時的任務
if 'my_logs' not in st.session_state:
    st.session_state.my_logs = [] # 存放已結束的紀錄

# --- 3. 標題與輸入區 ---
st.title("⏱️ 獨立生產工時追蹤系統")
st.info("此程式為獨立運行，資料不會上傳至雲端資料庫。")

with st.container():
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        oid = st.text_input("📦 錄入製令編號", placeholder="例如: 26M0103-01", key="input_oid")
    with c2:
        proc = st.selectbox("🛠️ 選擇執行工序", ["骨架作業", "前置作業", "配電作業", "模組作業", "通電作業", "IPQC查檢"])
    with c3:
        st.write(" ") 
        if st.button("➕ 加入看板", type="primary"):
            if oid:
                t_key = (oid, proc)
                if t_key not in st.session_state.my_tasks:
                    st.session_state.my_tasks[t_key] = {'status': 'stop', 'accumulated': 0, 'start_time': None}
            else:
                st.error("請輸入製令編號")

st.divider()

# --- 4. 自動刷新機制 (關鍵：讓秒數動起來) ---
# 如果有任何任務正在 running，每 1 秒強制頁面重繪
if any(t['status'] == 'running' for t in st.session_state.my_tasks.values()):
    time.sleep(1)
    st.rerun()

# --- 5. 任務監控看板 (依製令分組) ---
st.subheader("📅 目前執行看板")
unique_orders = sorted(list(set([k[0] for k in st.session_state.my_tasks.keys()])))

for o_id in unique_orders:
    with st.expander(f"📦 製令：{o_id}", expanded=True):
        # 找出該製令下的所有工序
        procs = [k for k in st.session_state.my_tasks.keys() if k[0] == o_id]
        
        for k in procs:
            p_name = k[1]
            task = st.session_state.my_tasks[k]
            
            # 計算當前秒數
            current_sec = task['accumulated']
            if task['status'] == 'running':
                current_sec += time.time() - task['start_time']
            
            # 格式化時間
            t_str = time.strftime("%H:%M:%S", time.gmtime(current_sec))
            
            # 顯示卡片
            st.markdown(f"""
                <div class="timer-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><b style="font-size:1.2rem;">🛠️ {p_name}</b></div>
                        <div class="timer-display">{t_str}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 控制按鈕 (確保 key 唯一)
            b1, b2, b3, b4 = st.columns(4)
            b_id = f"{o_id}_{p_name}"
            
            with b1:
                if task['status'] != 'running':
                    if st.button(f"▶️ 開始", key=f"btn_start_{b_id}"):
                        task['status'] = 'running'
                        task['start_time'] = time.time()
                        st.rerun()
            with b2:
                if task['status'] == 'running':
                    if st.button(f"⏸️ 暫停", key=f"btn_pause_{b_id}"):
                        task['accumulated'] += time.time() - task['start_time']
                        task['status'] = 'paused'
                        st.rerun()
            with b3:
                if st.button(f"⏹️ 結束", key=f"btn_stop_{b_id}"):
                    final_val = task['accumulated'] + (time.time() - task['start_time'] if task['status'] == 'running' else 0)
                    # 存入 Log
                    st.session_state.my_logs.append({'製令': o_id, '工序': p_name, '秒數': final_val})
                    del st.session_state.my_tasks[k]
                    st.rerun()
            with b4:
                if st.button(f"🗑️ 刪除", key=f"btn_del_{b_id}"):
                    del st.session_state.my_tasks[k]
                    st.rerun()

# --- 6. 統計報表 (自動累加相同製令工序) ---
st.divider()
st.subheader("📊 工時累計報表")

if st.session_state.my_logs:
    df = pd.DataFrame(st.session_state.my_logs)
    # 同樣製令的工序統計累加在一起
    summary = df.groupby(['製令', '工序'])['秒數'].sum().reset_index()
    summary['累計分鐘'] = (summary['秒數'] / 60).round(2)
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.write("📋 數據明細")
        st.dataframe(summary[['製令', '工序', '累計分鐘']], use_container_width=True)
    with col_b:
        st.write("📈 分佈圖表")
        st.bar_chart(data=summary, x="工序", y="累計分鐘", color="製令")
    
    if st.button("🧹 清空所有統計"):
        st.session_state.my_logs = []
        st.rerun()
else:
    st.info("目前的統計紀錄是空的。請在上方看板按下「結束」按鈕來產生數據。")
