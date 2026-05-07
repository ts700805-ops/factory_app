import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="獨立工時計時系統", layout="wide")

# 專業美化 CSS (確保卡片顯示正常)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .timer-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 15px;
        border-left: 6px solid #1E3A8A;
    }
    .timer-display {
        font-family: 'Courier New', monospace; font-size: 2rem; 
        color: #ef4444; font-weight: 900; text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化儲存空間 ---
if 'my_tasks' not in st.session_state:
    st.session_state.my_tasks = {} 
if 'my_logs' not in st.session_state:
    st.session_state.my_logs = [] 

# --- 3. 標題與輸入區 ---
st.title("⏱️ 獨立生產工時追蹤系統")

with st.container():
    # 這裡建立輸入欄位
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        oid = st.text_input("📦 錄入製令編號", placeholder="例如: 26M0103-01")
    with c2:
        proc = st.selectbox("🛠️ 選擇執行工序", ["骨架作業", "前置作業", "配電作業", "模組作業", "通電作業", "IPQC查檢"])
    with c3:
        st.write(" ") # 補位
        if st.button("➕ 加入看板", type="primary"):
            if oid:
                # 以 (製令, 工序) 作為唯一的 Key
                t_key = (oid, proc)
                if t_key not in st.session_state.my_tasks:
                    st.session_state.my_tasks[t_key] = {'status': 'stop', 'accumulated': 0, 'start_time': None}
                    st.rerun() # 立即刷新顯示新任務
            else:
                st.error("請輸入製令編號")

st.divider()

# --- 4. 自動刷新 (讓秒數動起來) ---
if any(t['status'] == 'running' for t in st.session_state.my_tasks.values()):
    time.sleep(1)
    st.rerun()

# --- 5. 任務監控看板 ---
st.subheader("📅 目前執行看板")
u_orders = sorted(list(set([k[0] for k in st.session_state.my_tasks.keys()])))

if not u_orders:
    st.info("💡 目前沒有進行中的任務，請在上方輸入資料並點擊「加入看板」。")

for o_id in u_orders:
    with st.expander(f"📦 製令：{o_id}", expanded=True):
        procs = [k for k in st.session_state.my_tasks.keys() if k[0] == o_id]
        for k in procs:
            p_name = k[1]
            task = st.session_state.my_tasks[k]
            
            # 計算當前秒數
            cur_sec = task['accumulated']
            if task['status'] == 'running':
                cur_sec += time.time() - task['start_time']
            
            t_str = time.strftime("%H:%M:%S", time.gmtime(cur_sec))
            
            # 顯示卡片 UI
            st.markdown(f"""
                <div class="timer-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><b style="font-size:1.2rem;">🛠️ {p_name}</b></div>
                        <div class="timer-display">{t_str}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 控制按鈕
            b1, b2, b3, b4 = st.columns(4)
            b_id = f"{o_id}_{p_name}".replace(" ", "_")
            
            with b1:
                if task['status'] != 'running':
                    if st.button(f"▶️ 開始", key=f"s_{b_id}"):
                        task['status'] = 'running'
                        task['start_time'] = time.time()
                        st.rerun()
            with b2:
                if task['status'] == 'running':
                    if st.button(f"⏸️ 暫停", key=f"p_{b_id}"):
                        task['accumulated'] += time.time() - task['start_time']
                        task['status'] = 'paused'
                        st.rerun()
            with b3:
                if st.button(f"⏹️ 結束", key=f"e_{b_id}"):
                    final = task['accumulated'] + (time.time() - task['start_time'] if task['status'] == 'running' else 0)
                    st.session_state.my_logs.append({'製令': o_id, '工序': p_name, '秒數': final})
                    del st.session_state.my_tasks[k]
                    st.rerun()
            with b4:
                if st.button(f"🗑️ 刪除", key=f"d_{b_id}"):
                    del st.session_state.my_tasks[k]
                    st.rerun()

# --- 6. 統計累加報表 ---
st.divider()
st.subheader("📊 工時累計報表")

if st.session_state.my_logs:
    df = pd.DataFrame(st.session_state.my_logs)
    summary = df.groupby(['製令', '工序'])['秒數'].sum().reset_index()
    summary['累計分鐘'] = (summary['秒數'] / 60).round(2)
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.dataframe(summary[['製令', '工序', '累計分鐘']], use_container_width=True)
    with col_b:
        st.bar_chart(data=summary, x="工序", y="累計分鐘", color="製令")
else:
    st.write("暫無已完成的工時紀錄。")
