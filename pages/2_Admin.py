import streamlit as st
import pandas as pd
from io import BytesIO
from db import (
    init_db,
    upsert_students,
    list_questions,
    update_question,
    create_question,
    delete_question,
    list_students,
    update_student,
    delete_student,
    export_responses_as_rows,
    reset_responses_and_completion,
    reset_questions_to_new_default,
)

st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")

init_db()

st.title("🛠️ Admin")

with st.sidebar:
    st.header("Đăng nhập Admin")
    user = st.text_input("Username", value=st.session_state.get("admin_user", ""))
    pwd = st.text_input("Password", type="password")
    do_login = st.button("Đăng nhập")

if do_login:
    if user == "admin" and pwd == "admin123":
        st.session_state["admin_auth"] = True
        st.session_state["admin_user"] = user
        st.success("Đăng nhập thành công.")
    else:
        st.session_state["admin_auth"] = False
        st.error("Sai thông tin đăng nhập.")

if not st.session_state.get("admin_auth"):
    st.warning("Vui lòng đăng nhập để sử dụng chức năng quản trị.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📥 Import/Export", "📝 Câu hỏi & Thang đo", "👥 Sinh viên", "♻️ Reset dữ liệu"]) 

with tab1:
    st.subheader("Import danh sách sinh viên + điểm thi vấn đáp (Excel)")
    st.caption("Cột yêu cầu: **Mã sinh viên**, **Email**, **Họ và tên**, **Điểm thi vấn đáp**")
    file = st.file_uploader("Chọn file Excel", type=["xlsx"])
    if file is not None:
        df = pd.read_excel(file)
        required_cols = ["Mã sinh viên", "Email", "Họ và tên", "Điểm thi vấn đáp"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Thiếu cột. Yêu cầu: {required_cols}")
        else:
            rows = []
            for _, r in df.iterrows():
                rows.append({
                    "msv": str(r["Mã sinh viên"]).strip(),
                    "email": str(r["Email"]).strip(),
                    "name": str(r["Họ và tên"]).strip(),
                    "score": float(r["Điểm thi vấn đáp"]),
                })
            upsert_students(rows)
            st.success(f"Đã import {len(rows)} sinh viên.")

    st.divider()
    st.subheader("Export dữ liệu phản hồi (CSV)")
    if st.button("Tải xuống responses.csv"):
        rows = export_responses_as_rows()
        out_df = pd.DataFrame(rows)
        buf = BytesIO()
        out_df.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button("Download responses.csv", data=buf.getvalue(), file_name="responses.csv", mime="text/csv")

with tab2:
    st.subheader("Danh sách câu hỏi & cấu hình thang đo")
    st.caption("Có thể thêm nhóm, thêm câu hỏi, đổi kiểu trả lời (slider hoặc open)")

    # Tạo câu hỏi mới
    with st.expander("➕ Tạo câu hỏi mới", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            new_group = st.text_input("Nhóm (ví dụ: Nhóm 1 – Nội dung khóa học / Buổi thi)")
            new_text = st.text_area("Nội dung câu hỏi")
        with c2:
            new_qtype = st.selectbox("Kiểu trả lời", options=["slider", "open"], index=0)
            order_no = st.number_input("Thứ tự", min_value=1, step=1, value=1)
        low = mid = high = None
        if new_qtype == "slider":
            c3, c4, c5 = st.columns(3)
            with c3:
                low = st.text_input("Nhãn mức 1", value="Thấp")
            with c4:
                mid = st.text_input("Nhãn mức 2", value="Trung bình")
            with c5:
                high = st.text_input("Nhãn mức 3", value="Cao")
        if st.button("Tạo câu hỏi"):
            try:
                create_question(text=new_text, group_name=new_group, qtype=new_qtype, low=low, mid=mid, high=high, order_no=order_no)
                st.success("Đã tạo câu hỏi mới.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    st.divider()
    # Quản lý danh sách câu hỏi hiện có
    qs = list_questions()
    for q in qs:
        with st.expander(f"[{q['order_no']}] {q['text']}  •  ({q['qtype']})", expanded=False):
            new_group = st.text_input("Nhóm", value=q["group_name"], key=f"g_{q['id']}")
            new_text = st.text_input("Sửa nội dung câu hỏi", value=q["text"], key=f"t_{q['id']}")
            qtype_new = st.selectbox("Kiểu trả lời", options=["slider", "open"], index=0 if q["qtype"]=="slider" else 1, key=f"qt_{q['id']}")
            if qtype_new == "slider":
                c1, c2, c3 = st.columns(3)
                with c1:
                    low = st.text_input("Nhãn mức 1 (low)", value=q.get("low_label") or "", key=f"l_{q['id']}")
                with c2:
                    mid = st.text_input("Nhãn mức 2 (mid)", value=q.get("mid_label") or "", key=f"m_{q['id']}")
                with c3:
                    high = st.text_input("Nhãn mức 3 (high)", value=q.get("high_label") or "", key=f"h_{q['id']}")
            else:
                low = mid = high = None
            c4, c5 = st.columns([1,1])
            with c4:
                if st.button("Lưu", key=f"s_{q['id']}"):
                    update_question(q["id"], text=new_text, low=low, mid=mid, high=high, group_name=new_group, qtype=qtype_new)
                    st.success("Đã cập nhật.")
            with c5:
                if st.button("Xóa", key=f"d_{q['id']}"):
                    delete_question(q["id"])
                    st.warning("Đã xóa câu hỏi.")

with tab3:
    st.subheader("Danh sách sinh viên")
    students = list_students()
    if students:
        df = pd.DataFrame(students)
        st.dataframe(df, hide_index=True)
        with st.expander("✏️ Sửa sinh viên"):
            msv = st.text_input("Mã sinh viên")
            email = st.text_input("Email mới", "")
            name = st.text_input("Họ tên mới", "")
            score = st.number_input("Điểm thi vấn đáp", step=0.1, format="%.1f")
            if st.button("Cập nhật"):
                update_student(msv, email if email else None, name if name else None, score if score else None)
                st.success("Đã cập nhật.")
        with st.expander("🗑️ Xóa sinh viên"):
            msv_del = st.text_input("Mã sinh viên cần xóa")
            if st.button("Xóa sinh viên"):
                delete_student(msv_del)
                st.warning("Đã xóa sinh viên và phản hồi liên quan.")
    else:
        st.info("Chưa có sinh viên trong hệ thống.")

with tab4:
    st.subheader("Reset dữ liệu khảo sát")
    st.caption("Xóa toàn bộ phản hồi và đánh dấu chưa hoàn thành cho tất cả sinh viên")
    if st.button("♻️ Reset responses + completed"):
        reset_responses_and_completion()
        st.success("Đã reset dữ liệu khảo sát.")
    st.divider()
    st.caption("Cập nhật lại bộ câu hỏi mặc định theo phiên bản mới (xóa hết câu hỏi & phản hồi hiện tại)")
    if st.button("🗃️ Reset questions theo bộ mới"):
        reset_questions_to_new_default()
        st.success("Đã cập nhật bộ câu hỏi mới.")
