import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="工時追蹤系統", layout="wide")

# 自定義 CSS (美化)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .status-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;
        border-left: 5px solid #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

# --- 初始化 Session State ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = {} 
if 'logs' not in st.session_state:
    st.session_state.logs = [] 

# --- 標題 ---
st.title("⏱️ 專業工時統計管理系統")

# --- 第一部分：輸入區 ---
with st.container():
    st.subheader("🆕 新增/搜尋任務")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        order_id = st.text_input("輸入製令編號", placeholder="例如: 26M0041-01")
    with c2:
        process_name = st.selectbox("選擇工序", ["骨架作業", "前置作業", "配電作業", "模組作業", "通電作業"])
    with c3:
        st.write(" ") 
        if st.button("➕ 加入看板", type="primary"):
            if order_id:
                # 使用 tuple 作為 key: (製令, 工序)
                task_key = (order_id, process_name)
                if task_key not in st.session_state.tasks:
                    st.session_state.tasks[task_key] = {
                        'status': 'stop', 
                        'total_time': 0, 
                        'start_at': None
                    }
            else:
                st.warning("請輸入製令編號")

st.divider()

# --- 第二部分：任務監控看板 ---
st.subheader("📅 目前執行看板")

# 按製令排序顯示
unique_orders = sorted(list(set([k[0] for k in st.session_state.tasks.keys()])))

# 如果有正在運行的任務，啟動自動重新整理（每 1 秒重新載入一次畫面，讓時間動起來）
if any(t['status'] == 'running' for t in st.session_state.tasks.values()):
    time.sleep(1) # 稍微延遲避免過度佔用 CPU
    st.rerun()

for o_id in unique_orders:
    with st.expander(f"📦 製令：{o_id}", expanded=True):
        target_procs = [k for k in st.session_state.tasks.keys() if k[0] == o_id]
        
        for key in target_procs:
            proc_name = key[1]
            task = st.session_state.tasks[key]
            
            # 計算目前累計總秒數
            display_seconds = task['total_time']
            if task['status'] == 'running':
                display_seconds += time.time() - task['start_at']
            
            # 轉換格式
            time_str = time.strftime("%H:%M:%S", time.gmtime(display_seconds))
            
            # 卡片顯示
            st.markdown(f"""<div class="status-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: bold; color:#333;">🛠️ {proc_name}</span>
                    <span style="font-family: 'Courier New', monospace; font-size: 1.8rem; color: #ef4444; font-weight: 900;">{time_str}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            
            # 按鈕控制 (key 必須全球唯一，用 key 組合)
            b1, b2, b3, b4 = st.columns(4)
            
            # 組合一個唯一的 key ID 防止錯誤
            btn_id = f"{key[0]}_{key[1]}"

            with b1: # 開始/繼續
                if task['status'] != 'running':
                    if st.button(f"▶️ 開始", key=f"start_{btn_id}"):
                        task['status'] = 'running'
                        task['start_at'] = time.time()
                        st.rerun()
            
            with b2: # 暫停
                if task['status'] == 'running':
                    if st.button(f"⏸️ 暫停", key=f"pause_{btn_id}"):
                        task['total_time'] += time.time() - task['start_at']
                        task['status'] = 'paused'
                        st.rerun()
            
            with b3: # 結束
                if st.button(f"⏹️ 結束", key=f"stop_{btn_id}"):
                    final_sec = task['total_time']
                    if task['status'] == 'running':
                        final_sec += time.time() - task['start_at']
                    
                    st.session_state.logs.append({
                        '製令': o_id,
                        '工序': proc_name,
                        '工時(秒)': round(final_sec, 2),
                        '結束時間': datetime.now().strftime("%H:%M:%S")
                    })
                    del st.session_state.tasks[key]
                    st.rerun()

            with b4: # 刪除
                if st.button(f"🗑️ 刪除", key=f"del_{btn_id}"):
                    del st.session_state.tasks[key]
                    st.rerun()

# --- 第三部分：統計分析 ---
st.divider()
st.subheader("📊 工時累計報表")

if st.session_state.logs:
    df_logs = pd.DataFrame(st.session_state.logs)
    
    # 核心功能：同樣製令與工序累加
    summary = df_logs.groupby(['製令', '工序'])['工時(秒)'].sum().reset_index()
    summary['分鐘'] = (summary['工時(秒)'] / 60).round(2)
    
    col_tab, col_chart = st.columns([1, 1])
    with col_tab:
        st.write("📋 累計數據明細")
        st.table(summary[['製令', '工序', '分鐘']])
    with col_chart:
        st.write("📈 產能分配圖")
        st.bar_chart(data=summary, x="工序", y="分鐘", color="製令")
    
    if st.button("🧹 清除所有紀錄"):
        st.session_state.logs = []
        st.rerun()
else:
    st.info("尚無結案資料。請在上方看板按下「結束」按鈕來產生統計。")
