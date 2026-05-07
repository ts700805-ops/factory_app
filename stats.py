import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="工時追蹤系統", layout="wide")

# 自定義 CSS 讓介面更專業
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .status-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;
        border-left: 5px solid #1E3A8A;
    }
    .metric-box {
        background-color: #e9ecef; padding: 10px; border-radius: 5px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 初始化 Session State (儲存計時資料) ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = {} # 格式: { (製令, 工序): {status: 'stop', total_time: 0, start_at: None} }
if 'logs' not in st.session_state:
    st.session_state.logs = [] # 儲存已完成的歷史紀錄

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
        st.write(" ") # 補位
        if st.button("➕ 加入看板", type="primary"):
            if order_id:
                key = (order_id, process_name)
                if key not in st.session_state.tasks:
                    st.session_state.tasks[key] = {
                        'status': 'stop', 
                        'total_time': 0, 
                        'start_at': None,
                        'paused_time': 0
                    }
            else:
                st.warning("請輸入製令編號")

st.divider()

# --- 第二部分：任務監控看板 ---
st.subheader("📅 目前執行看板")

# 按製令分群
unique_orders = sorted(list(set([k[0] for k in st.session_state.tasks.keys()])))

for o_id in unique_orders:
    with st.expander(f"📦 製令：{o_id}", expanded=True):
        # 找出屬於該製令的所有工序
        target_procs = [k for k in st.session_state.tasks.keys() if k[0] == o_id]
        
        for key in target_procs:
            proc_name = key[1]
            task = st.session_state.tasks[key]
            
            # 計算顯示時間
            current_elapsed = task['total_time']
            if task['status'] == 'running':
                current_elapsed += time.time() - task['start_at']
            
            # 轉換為 時:分:秒
            time_str = time.strftime("%H:%M:%S", time.gmtime(current_elapsed))
            
            # 介面卡片
            st.markdown(f"""<div class="status-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.2rem; font-weight: bold;">🛠️ {proc_name}</span>
                    <span style="font-family: monospace; font-size: 1.5rem; color: #ef4444;">{time_str}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            
            # 按鈕控制區
            b1, b2, b3, b4 = st.columns(4)
            
            with b1: # 開始/繼續
                if task['status'] != 'running':
                    if st.button(f"▶️ 開始", key=f"start_{key}"):
                        task['status'] = 'running'
                        task['start_at'] = time.time()
                        st.rerun()
            
            with b2: # 暫停
                if task['status'] == 'running':
                    if st.button(f"⏸️ 暫停", key=f"pause_{key}"):
                        task['total_time'] += time.time() - task['start_at']
                        task['status'] = 'paused'
                        st.rerun()
            
            with b3: # 結束並累加
                if st.button(f"⏹️ 結束", key=f"stop_{key}"):
                    final_time = task['total_time']
                    if task['status'] == 'running':
                        final_time += time.time() - task['start_at']
                    
                    # 存入歷史紀錄
                    st.session_state.logs.append({
                        '製令': o_id,
                        '工序': proc_name,
                        '工時(秒)': round(final_time, 2),
                        '結束時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    del st.session_state.tasks[key]
                    st.success(f"{proc_name} 已結案")
                    st.rerun()

            with b4: # 刪除
                if st.button(f"🗑️ 刪除", key=f"del_{key}"):
                    del st.session_state.tasks[key]
                    st.rerun()

# --- 第三部分：工時累加統計 ---
st.divider()
st.subheader("📊 工時統計累加報表")

if st.session_state.logs:
    log_df = pd.DataFrame(st.session_state.logs)
    
    # 計算每個製令/工序的總時數 (秒轉分鐘)
    summary_df = log_df.groupby(['製令', '工序'])['工時(秒)'].sum().reset_index()
    summary_df['總工時(分鐘)'] = (summary_df['工時(秒)'] / 60).round(2)
    
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.dataframe(summary_df[['製令', '工序', '總工時(分鐘)']], use_container_width=True)
    with c_right:
        # 圖表展示
        st.bar_chart(data=summary_df, x="工序", y="總工時(分鐘)", color="製令")
        
    if st.button("🧹 清空所有統計紀錄"):
        st.session_state.logs = []
        st.rerun()
else:
    st.info("尚未有結束的工序資料，統計圖表將在您按下「結束」後產生。")
