import streamlit as st
import pandas as pd
import time
import os  # 新增：用於檢查檔案是否存在
from datetime import datetime

st.set_page_config(page_title="獨立工時追蹤", layout="wide")

# --- 設定本地儲存檔案名稱 ---
DATA_FILE = "work_log.csv"

# --- 1. 初始化與讀取舊有資料 ---
# 檢查檔案是否存在，存在就讀取，不存在就建立空的 list
if 'tasks' not in st.session_state:
    st.session_state.tasks = {} 

if 'logs' not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.logs = pd.read_csv(DATA_FILE).to_dict('records')
    else:
        st.session_state.logs = []

# --- 2. 介面與輸入邏輯 (維持不變) ---
st.title("⏱️ 獨立工時統計管理系統 (資料存於本地)")

with st.container():
    st.subheader("🆕 新增任務")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        order_id = st.text_input("輸入製令編號", placeholder="例如: 26M0041-01")
    with c2:
        process_name = st.selectbox("選擇工序", ["骨架作業", "前置作業", "配電作業", "模組作業", "通電作業"])
    with c3:
        st.write(" ") 
        if st.button("➕ 加入看板", type="primary"):
            if order_id:
                task_key = (order_id, process_name)
                if task_key not in st.session_state.tasks:
                    st.session_state.tasks[task_key] = {'status': 'stop', 'total_time': 0, 'start_at': None}
            else:
                st.warning("請輸入製令編號")

st.divider()

# --- 3. 任務監控看板 (加入自動刷新) ---
if any(t['status'] == 'running' for t in st.session_state.tasks.values()):
    time.sleep(1)
    st.rerun()

unique_orders = sorted(list(set([k[0] for k in st.session_state.tasks.keys()])))

for o_id in unique_orders:
    with st.expander(f"📦 製令：{o_id}", expanded=True):
        target_procs = [k for k in st.session_state.tasks.keys() if k[0] == o_id]
        for key in target_procs:
            proc_name = key[1]
            task = st.session_state.tasks[key]
            display_seconds = task['total_time']
            if task['status'] == 'running':
                display_seconds += time.time() - task['start_at']
            
            time_str = time.strftime("%H:%M:%S", time.gmtime(display_seconds))
            st.markdown(f"**🛠️ {proc_name}** ➔ <span style='color:red; font-size:20px;'>{time_str}</span>", unsafe_allow_html=True)
            
            b1, b2, b3, b4 = st.columns(4)
            btn_id = f"{key[0]}_{key[1]}"

            with b1:
                if task['status'] != 'running' and st.button(f"▶️ 開始", key=f"s_{btn_id}"):
                    task['status'] = 'running'; task['start_at'] = time.time(); st.rerun()
            with b2:
                if task['status'] == 'running' and st.button(f"⏸️ 暫停", key=f"p_{btn_id}"):
                    task['total_time'] += time.time() - task['start_at']
                    task['status'] = 'paused'; st.rerun()
            with b3:
                if st.button(f"⏹️ 結束", key=f"e_{btn_id}"):
                    final_sec = task['total_time'] + (time.time() - task['start_at'] if task['status'] == 'running' else 0)
                    new_record = {
                        '製令': o_id, '工序': proc_name, 
                        '工時(秒)': round(final_sec, 2), 
                        '結束時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.logs.append(new_record)
                    # --- 關鍵：存入本地檔案 ---
                    pd.DataFrame(st.session_state.logs).to_csv(DATA_FILE, index=False)
                    del st.session_state.tasks[key]
                    st.rerun()
            with b4:
                if st.button(f"🗑️ 刪除", key=f"d_{btn_id}"):
                    del st.session_state.tasks[key]; st.rerun()

# --- 4. 統計報表 ---
st.divider()
st.subheader("📊 累計工時報表 (已自動存檔)")

if st.session_state.logs:
    df_logs = pd.DataFrame(st.session_state.logs)
    summary = df_logs.groupby(['製令', '工序'])['工時(秒)'].sum().reset_index()
    summary['分鐘'] = (summary['工時(秒)'] / 60).round(2)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.table(summary[['製令', '工序', '分鐘']])
    with col2:
        st.bar_chart(data=summary, x="工序", y="分鐘", color="製令")
    
    if st.button("🧹 清空所有歷史紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.session_state.logs = []
        st.rerun()
else:
    st.info("尚無數據，請先新增任務並點擊「結束」。")
