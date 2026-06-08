import streamlit as st
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

# 2. 初始化 Session State
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "user" not in st.session_state:
    st.session_state.user = None

# 3. 側邊欄導航 (確保縮排層級嚴格對齊)
def render_sidebar():
    st.sidebar.markdown(f"### 👤 當前人員：**{st.session_state.user}**")
    
    # 導航選項列表
    nav_options = [
        "📊 製造部派工專區",
        "🧾 組長待辦事項",
        "💡 2026上半年技能考核進度",
        "📝 每日6S任務回報",
        "⚙️ 管理後台"
    ]
    
    # 計算 index 以便維持選取狀態
    current_index = nav_options.index(st.session_state.menu_selection) if st.session_state.menu_selection in nav_options else 0
    
    # 這裡確保導航列的縮排是乾淨的
    nav = st.sidebar.radio("功能導航", nav_options, index=current_index)
    
    # 登出按鈕
    if st.sidebar.button("🚪 點此登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    return nav

# 4. 主程式執行邏輯
if st.session_state.user is None:
    # 簡易登入頁面
    st.title("⚓ 超慧科技管理系統")
    user_name = st.selectbox("請選擇組長姓名登入", ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"])
    if st.button("確認登入"):
        st.session_state.user = user_name
        st.rerun()
else:
    # 渲染導航並取得結果
    nav = render_sidebar()
    
    # 如果導航改變則重整頁面
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    # 5. 頁面內容路由
    st.title(f"當前功能：{st.session_state.menu_selection}")
    
    if st.session_state.menu_selection == "🧾 組長待辦事項":
        st.write("這是您的待辦事項頁面。")
        # 這裡放入您想測試的表格或清單
        tasks = pd.DataFrame({
            "項目": ["設備維護", "人員考核", "庫存盤點"],
            "優先級": ["高", "中", "低"]
        })
        st.table(tasks)
        
    elif st.session_state.menu_selection == "📊 製造部派工專區":
        st.write("這裡是派工區...")
    
    # 其他頁面邏輯可在此延伸...
