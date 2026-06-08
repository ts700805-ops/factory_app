# ==========================================
# 📘 頁面：標準SOP功能 (百分之百防呆修復版)
# ==========================================
    elif st.session_state.menu_selection == "📘 標準SOP功能":
        import base64
        import re

        # 直接在功能內部定義好路徑，百分之百不會再噴 NameError 錯誤！
        SOP_LIST_URL = f"{DB_BASE_URL}/sop_settings"      # 儲存 SOP 下拉選單工序項目
        SOP_FILE_URL = f"{DB_BASE_URL}/sop_file_data"     # 儲存各工序對應的 PDF 檔案內容

        st.markdown('<h1 style="text-align:center; color:#38bdf8; font-weight:900; font-size:2.5rem;">📘 標準 SOP 線上查閱中心</h1>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#cbd5e1;'>依據工序查詢對應標準作業書，支援線上直接查閱與動態管理</p>", unsafe_allow_html=True)
        st.divider()

        # 1. 讀取與初始化 Firebase 後台工序選單資料
        sop_settings = requests.get(f"{SOP_LIST_URL}.json").json() or {"sop_types": []}
        sop_types = sop_settings.get("sop_types", ["骨架作業", "前置作業", "配電作業"]) # 預設保底選單

        col_left, col_right = st.columns([1.2, 2.0])

        # --- 左側：選單項目編輯與工序切換 ---
        with col_left:
            st.markdown("### ⚙️ SOP 下拉選單管理")
            with st.container(border=True):
                current_sop_str = "，".join(sop_types)
                sop_input = st.text_area("編輯工序下拉選單 (請以逗號或分行隔開)", value=current_sop_str, height=150, help="修改此處可動態調整下方的工序選擇清單")
                
                if st.button("💾 儲存選單項目", use_container_width=True, type="primary", key="save_sop_list_btn"):
                    # 同步支援中英文逗號與換行拆分
                    new_sop_list = [t.strip() for t in re.split(r'[，,\n]', sop_input) if t.strip()]
                    requests.put(f"{SOP_LIST_URL}.json", data=json.dumps({"sop_types": new_sop_list}))
                    st.success("✅ 下拉選單項目已成功更新！")
                    time.sleep(0.5)
                    st.rerun()

            st.write("")
            st.markdown("### 🎯 第一步：選擇查閱工序")
            selected_sop_proc = st.selectbox("請選擇當前要查閱或指派的製造工序：", options=sop_types, key="main_sop_selectbox")

        # --- 右側：PDF 檔案上傳與即時看板顯示 ---
        with col_right:
            # 💡 【核心修復關鍵】安全防呆：若選單暫時抓不到值，直接不往下執行或給予保底值，避免噴出 AttributeError
            if not selected_sop_proc:
                st.warning("⏳ 正在載入工序資料，請稍候...")
            else:
                st.markdown(f"### 📑 工序：【{selected_sop_proc}】SOP 文件管理")
                
                # 從資料庫抓取此工序目前有沒有存過的 PDF
                # 針對特殊字元與中文進行安全編碼，避免 Firebase 路徑報錯
                safe_proc_key = base64.b64encode(selected_sop_proc.encode('utf-8')).decode('utf-8').replace('=', '')
                
                existing_file_data = requests.get(f"{SOP_FILE_URL}/{safe_proc_key}.json").json()

                # 提供上傳元件
                uploaded_pdf = st.file_uploader(f"📤 上傳或更新【{selected_sop_proc}】的 SOP (限制 PDF 格式)", type=["pdf"], key=f"file_uploader_{safe_proc_key}")
                
                if uploaded_pdf is not None:
                    if st.button("🚀 確定上傳並覆蓋舊檔案", use_container_width=True):
                        with st.spinner("檔案封裝傳輸中，請稍候..."):
                            # 將 PDF 檔案轉為 Base64 字串以存入 Realtime Database
                            file_bytes = uploaded_pdf.read()
                            base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                            
                            payload = {
                                "file_name": uploaded_pdf.name,
                                "upload_time": get_now_str(),
                                "uploader": st.session_state.user if "user" in st.session_state else "系統管理員",
                                "file_base64": base64_pdf
                            }
                            
                            # 寫入 Firebase
                            requests.put(f"{SOP_FILE_URL}/{safe_proc_key}.json", data=json.dumps(payload))
                            st.success(f"🎉 【{uploaded_pdf.name}】已成功與【{selected_sop_proc}】關聯儲存！")
                            time.sleep(0.8)
                            st.rerun()

                st.divider()
                st.markdown("### 🔍 SOP 現場即時看板")

                if existing_file_data and "file_base64" in existing_file_data:
                    st.info(f"📄 目前文件：**{existing_file_data.get('file_name')}** 💾 登記人：{existing_file_data.get('uploader','系統')} ({existing_file_data.get('upload_time')})")
                    
                    # 刪除檔案功能 (含安全密碼驗證)
                    with st.expander("🗑️ 刪除此工序之 SOP 文件"):
                        pwd_sop = st.text_input("請輸入管理權限密碼：", type="password", key=f"pwd_sop_{safe_proc_key}")
                        if st.button("❌ 確認徹底移除此 PDF 檔案", type="primary", use_container_width=True, key=f"del_sop_btn_{safe_proc_key}"):
                            if pwd_sop == "0000":
                                requests.delete(f"{SOP_FILE_URL}/{safe_proc_key}.json")
                                st.success("檔案已成功從雲端資料庫抹除！")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ 密碼錯誤，拒絕刪除！")

                    # 在網頁上建立一個高質感的 PDF 內嵌式閱讀器
                    try:
                        pdf_b64 = existing_file_data["file_base64"]
                        # 建立 HTML iframe 來內嵌顯示 PDF
                        pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="800px" style="border: 2px solid #38bdf8; border-radius:10px;"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception as view_err:
                        st.error(f"無法載入預覽畫面: {view_err}。但您可以嘗試重新上傳檔案。")
                else:
                    st.warning(f"💡 目前【{selected_sop_proc}】尚未上傳任何標準 SOP 說明書。請於上方選擇 PDF 檔案進行指派。")
