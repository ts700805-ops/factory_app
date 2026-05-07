import streamlit as st
import pandas as pd
import plotly.express as px # 這是畫圖用的進階套件，若沒安裝可改用 st.bar_chart

st.set_page_config(page_title="獨立工時統計工具", layout="wide")

st.title("🛡️ 獨立工時統計系統 (測試版)")
st.write("這個程式與 app.py 完全分開，不會更動到正式資料庫。")

# --- 側邊欄：功能切換 ---
mode = st.sidebar.selectbox("選擇操作模式", ["手動輸入資料", "上傳 Excel/CSV 統計", "範例圖表展示"])

# --- 模式 1：手動輸入 (適合新手練習邏輯) ---
if mode == "手動輸入資料":
    st.header("✍️ 快速登記工時")
    with st.form("manual_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.selectbox("人員", ["張三", "李四", "王五"])
        with col2:
            proc = st.selectbox("工序", ["骨架組裝", "電路測試", "包裝"])
        with col3:
            hours = st.number_input("花費工時 (小時)", min_value=0.5, step=0.5)
        
        submit = st.form_submit_button("暫存並統計")
        
    if submit:
        # 這裡僅演示，因為沒連資料庫，重整頁面會消失
        st.success(f"已記錄：{name} 執行 {proc} 共 {hours} 小時")
        st.info("提示：若要永久儲存，此處未來可以改成寫入本地 CSV 檔。")

# --- 模式 2：上傳檔案 (最實用的功能) ---
elif mode == "上傳 Excel/CSV 統計":
    st.header("📂 上傳生產紀錄檔案")
    uploaded_file = st.file_uploader("請選擇你的 Excel 或 CSV 檔案", type=["csv", "xlsx"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("數據預覽：")
        st.dataframe(df.head())
        
        # 簡單統計
        st.subheader("📊 數據分析結果")
        # 假設你的檔案裡有「人員」和「工時」欄位
        try:
            st.bar_chart(df.set_index(df.columns[0])) # 抓第一欄當索引畫圖
        except:
            st.warning("檔案欄位格式不符，無法自動畫圖，請檢查標題列。")

# --- 模式 3：範例圖表 (看效果用) ---
elif mode == "範例圖表展示":
    st.header("📈 模擬產能報表")
    # 建立一些假數據
    chart_data = pd.DataFrame({
        "人員": ["陳小明", "林大華", "張阿三", "李四郎"],
        "總工時": [45, 52, 38, 41]
    })
    
    st.bar_chart(data=chart_data, x="人員", y="總工時")
    st.write("這是獨立程式的呈現效果，你可以隨意修改這裏的顏色和標題。")
