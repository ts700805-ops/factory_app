# --- 修正後的導航區塊 ---
st.sidebar.markdown(f"### 👤 當前人員：**{st.session_state.user}**")

# 1. 先將導航選項獨立出來定義，避免括號內部的縮排混亂
menu_options = [
    "📊 製造部派工專區",
    "🧾 組長待辦事項",
    "💡 2026上半年技能考核進度",
    "📝 每日6S任務回報",
    "⚙️ 管理後台"
]

# 2. 將列表變數直接傳入 radio
# 這樣寫 Python 就不會因為縮排對齊問題而報錯
nav = st.sidebar.radio("功能導航", menu_options)

# 3. 登出按鈕
if st.sidebar.button("🚪 點此登出系統", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# 4. 處理導航變更
if nav != st.session_state.menu_selection:
    st.session_state.menu_selection = nav
    st.rerun()
