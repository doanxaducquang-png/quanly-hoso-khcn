import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
from utils import (
    LIST_LINH_VUC, LIST_LOAI_HINH, LIST_HT_TRIEN_KHAI_1, LIST_HT_TRIEN_KHAI_2,
    LIST_HT_XET, LIST_PHAN_LOAI_CN, LIST_HOC_HAM, LIST_TRANG_THAI, LIST_NEN_TANG_SO,
    parse_bm09_word, load_data, save_new_record
)

st.set_page_config(page_title="Hệ thống Quản lý Hồ sơ KH&CN", page_icon="📊", layout="wide")

if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "show_validation_errors" not in st.session_state:
    st.session_state.show_validation_errors = False

st.title("📌 HỆ THỐNG QUẢN LÝ & BÁO CÁO HỒ SƠ ĐĂNG KÝ KH&CN")
st.markdown("---")

col_head1, col_head2 = st.columns([8, 2])
with col_head2:
    if st.button("🔄 Cập nhật dữ liệu từ Google Sheets"):
        st.cache_data.clear()
        st.rerun()

df_data = load_data()

tab_dashboard, tab_report, tab_search, tab_input = st.tabs([
    "📊 Dashboard Trực Quan", "📑 Báo Cáo Tổng Hợp", "🔍 Tra Cứu & Quản Lý Hồ Sơ", "➕ Nhập Hồ Sơ Mới"
])

# ---------------- TAB 1: DASHBOARD ----------------
with tab_dashboard:
    st.header("📊 DASHBOARD TỔNG QUAN")
    if df_data.empty:
        st.warning("Chưa có dữ liệu trong Google Sheets hoặc không thể kết nối.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng số hồ sơ", f"{len(df_data)} hồ sơ")
        c2.metric("Tổng kinh phí đề xuất", f"{df_data['Tổng kinh phí đề xuất (VNĐ)'].sum():,.0f} VNĐ")
        c3.metric("Kinh phí NSNN", f"{df_data['Kinh phí NSNN (VNĐ)'].sum():,.0f} VNĐ")
        c4.metric("Kinh phí Ngoài NSNN", f"{df_data['Kinh phí Ngoài NSNN (VNĐ)'].sum():,.0f} VNĐ")
        st.markdown("---")
        
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("1. Cơ cấu Kinh phí theo Lĩnh vực")
            df_lv = df_data.groupby("Lĩnh vực")[["Kinh phí NSNN (VNĐ)", "Kinh phí Ngoài NSNN (VNĐ)"]].sum().reset_index()
            fig_lv = px.bar(df_lv, x="Lĩnh vực", y=["Kinh phí NSNN (VNĐ)", "Kinh phí Ngoài NSNN (VNĐ)"], barmode="stack", text_auto='.2s')
            st.plotly_chart(fig_lv, use_container_width=True)

        with r1c2:
            st.subheader("2. Tỷ lệ Loại hình Nhiệm vụ")
            df_lh = df_data["Loại hình nhiệm vụ"].value_counts().reset_index()
            df_lh.columns = ["Loại hình", "Số lượng"]
            st.plotly_chart(px.pie(df_lh, names="Loại hình", values="Số lượng", hole=0.4), use_container_width=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("3. Trình độ Chủ nhiệm Đề tài")
            counts_hh = df_data["Học hàm, học vị"].value_counts()
            df_hh = pd.DataFrame({"Học hàm/Học vị": LIST_HOC_HAM})
            df_hh["Số lượng"] = df_hh["Học hàm/Học vị"].map(counts_hh).fillna(0).astype(int)
            st.plotly_chart(px.bar(df_hh, x="Học hàm/Học vị", y="Số lượng", text="Số lượng", color="Học hàm/Học vị"), use_container_width=True)

        with r2c2:
            st.subheader("4. Phân loại Chủ nhiệm")
            df_pl = df_data["Phân loại Chủ nhiệm"].value_counts().reset_index()
            df_pl.columns = ["Phân loại", "Số lượng"]
            st.plotly_chart(px.pie(df_pl, names="Phân loại", values="Số lượng"), use_container_width=True)

# ---------------- TAB 2: BÁO CÁO ----------------
with tab_report:
    st.header("📑 BÁO CÁO TỔNG HỢP HỒ SƠ")
    if not df_data.empty:
        st.subheader("I. TỔNG QUAN HỒ SƠ & KINH PHÍ")
        st.table(pd.DataFrame([
            {"Chỉ tiêu": "1. Tổng số hồ sơ tiếp nhận", "Giá trị": f"{len(df_data)} hồ sơ"},
            {"Chỉ tiêu": "2. Tổng kinh phí đề xuất", "Giá trị": f"{df_data['Tổng kinh phí đề xuất (VNĐ)'].sum():,.0f} VNĐ"},
            {"Chỉ tiêu": "3. Kinh phí NSNN", "Giá trị": f"{df_data['Kinh phí NSNN (VNĐ)'].sum():,.0f} VNĐ"},
            {"Chỉ tiêu": "4. Kinh phí Ngoài NSNN", "Giá trị": f"{df_data['Kinh phí Ngoài NSNN (VNĐ)'].sum():,.0f} VNĐ"},
        ]))

        st.subheader("II. THỐNG KÊ THEO LĨNH VỰC")
        df_lv_stat = [{
            "Lĩnh vực": lv, "Số lượng": len(df_data[df_data["Lĩnh vực"] == lv]),
            "Tổng kinh phí": f"{df_data[df_data['Lĩnh vực'] == lv]['Tổng kinh phí đề xuất (VNĐ)'].sum():,.0f}"
        } for lv in LIST_LINH_VUC]
        st.dataframe(pd.DataFrame(df_lv_stat), use_container_width=True)

# ---------------- TAB 3: TRA CỨU & XUẤT EXCEL ----------------
with tab_search:
    st.header("🔍 TRA CỨU HỒ SƠ & XUẤT DỮ LIỆU EXCEL")
    if not df_data.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_data.to_excel(writer, index=False, sheet_name='QUAN_LY_HO_SO')
        st.download_button("📥 Tải File Excel Dữ Liệu", data=buffer.getvalue(), file_name="QuanLy_DonDangKy_KHCN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        
        kw = st.text_input("🔑 Tìm kiếm tên nhiệm vụ / Chủ nhiệm:")
        df_filtered = df_data.copy()
        if kw:
            df_filtered = df_filtered[df_filtered["Tên nhiệm vụ / Cụm / Chuỗi"].astype(str).str.lower().str.contains(kw.lower())]
        st.dataframe(df_filtered, use_container_width=True)

# ---------------- TAB 4: NHẬP HỒ SƠ ----------------
with tab_input:
    st.header("➕ NHẬP HỒ SƠ MỚI")
    uploaded_docx = st.file_uploader("Tải lên file Word BM-09 (.docx):", type=["docx"])
    if uploaded_docx:
        try:
            st.session_state.form_data.update(parse_bm09_word(uploaded_docx))
            st.success("🎉 Đã đọc tự động file Word BM-09!")
        except Exception as e:
            st.error(f"Lỗi đọc file Word: {e}")

    fd = st.session_state.form_data
    next_stt = int(df_data["STT"].max() + 1) if not df_data.empty and "STT" in df_data.columns else 1
    
    st.subheader("Form Nhập Liệu Hồ Sơ")
    c1, c2 = st.columns(2)
    with c1:
        ten_nhiem_vu = st.text_area("Tên nhiệm vụ (*)", value=fd.get("ten_nhiem_vu", ""))
        linh_vuc = st.selectbox("Lĩnh vực (*)", LIST_LINH_VUC, index=LIST_LINH_VUC.index(fd.get("linh_vuc", LIST_LINH_VUC[0])))
        loai_hinh = st.selectbox("Loại hình (*)", LIST_LOAI_HINH, index=LIST_LOAI_HINH.index(fd.get("loai_hinh", LIST_LOAI_HINH[0])))
        ten_tc = st.text_input("Tên tổ chức chủ trì (*)", value=fd.get("ten_tc", ""))
        dc_tc = st.text_input("Địa chỉ (*)", value=fd.get("dc_tc", ""))
        dd_pl = st.text_input("Người đại diện pháp luật (*)", value=fd.get("dd_pl", ""))
        chuc_vu_dd = st.text_input("Chức vụ đại diện (*)", value=fd.get("chuc_vu_dd", ""))
    with c2:
        ho_ten_cn = st.text_input("Họ tên Chủ nhiệm (*)", value=fd.get("ho_ten_cn", ""))
        hoc_ham_hoc_vi = st.selectbox("Học hàm học vị (*)", LIST_HOC_HAM, index=LIST_HOC_HAM.index(fd.get("hoc_ham_hoc_vi", LIST_HOC_HAM[2])))
        don_vi_ct = st.text_input("Đơn vị công tác (*)", value=fd.get("don_vi_ct", ""))
        dt_cn = st.text_input("Điện thoại Chủ nhiệm (*)", value=fd.get("dt_cn", ""))
        tong_kinh_phi = st.number_input("Tổng kinh phí đề xuất (VNĐ) (*)", min_value=0.0, value=float(fd.get("tong_kinh_phi", 0.0)))
        kinh_phi_nsnn = st.number_input("Kinh phí NSNN (VNĐ)", min_value=0.0, value=float(fd.get("kinh_phi_nsnn", 0.0)))

    if st.button("💾 LƯU HỒ SƠ VÀO GOOGLE SHEETS", type="primary", use_container_width=True):
        if not ten_nhiem_vu or not ten_tc or not ho_ten_cn:
            st.error("🚫 Vui lòng điền đầy đủ các thông tin bắt buộc!")
        else:
            kinh_phi_ngoai = max(0.0, tong_kinh_phi - kinh_phi_nsnn)
            new_data = {
                "STT": next_stt, "Tên nhiệm vụ / Cụm / Chuỗi": ten_nhiem_vu, "Lĩnh vực": linh_vuc,
                "Loại hình nhiệm vụ": loai_hinh, "Tên tổ chức chủ trì": ten_tc, "Địa chỉ tổ chức": dc_tc,
                "Người đại diện pháp luật": dd_pl, "Chức vụ người đại diện": chuc_vu_dd, "Họ tên Chủ nhiệm": ho_ten_cn,
                "Học hàm, học vị": hoc_ham_hoc_vi, "Đơn vị công tác": don_vi_ct, "Điện thoại Chủ nhiệm": dt_cn,
                "Tổng kinh phí đề xuất (VNĐ)": tong_kinh_phi, "Kinh phí NSNN (VNĐ)": kinh_phi_nsnn,
                "Kinh phí Ngoài NSNN (VNĐ)": kinh_phi_ngoai, "Trạng thái hồ sơ": "Đang xét"
            }
            ok, msg = save_new_record(new_data)
            if ok:
                st.success(msg)
                st.balloons()
                st.session_state.form_data = {}
                st.rerun()
            else:
                st.error(msg)