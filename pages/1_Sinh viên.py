import streamlit as st
from db import init_db, get_student, list_questions, save_responses, mark_completed, create_otp, verify_otp, can_request_otp, get_student_responses
from utils_mail import send_email_code
import random

st.set_page_config(page_title="Sinh viên - Khảo sát", page_icon="👩‍🎓", layout="wide")

st.markdown("""
<style>
div[data-baseweb="slider"] > div > div[role="slider"] {
    background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60);
}
</style>
""", unsafe_allow_html=True)

st.title("👩‍🎓 Sinh viên")

init_db()

# ---------- Step 1: Request OTP ----------
with st.form("login_form"):
    st.subheader("Đăng nhập khảo sát (OTP qua email)")
    msv = st.text_input("Mã sinh viên").strip()
    email = st.text_input("Email (theo danh sách import)").strip()
    req = st.form_submit_button("Gửi mã xác thực")

if req:
    st.session_state["auth_msv"] = None
    st.session_state["otp_ready_for"] = None
    stu = get_student(msv)
    if not stu:
        st.error("❌ Không tìm thấy Mã sinh viên trong hệ thống.")
    elif email.lower() != (stu["email"] or "").lower():
        st.error("❌ Email không khớp dữ liệu. Vui lòng kiểm tra lại.")
    else:
        if not can_request_otp(msv):
            st.warning("Bạn vừa yêu cầu mã. Vui lòng đợi ~60 giây rồi thử lại.")
        else:
            code = f"{random.randint(0, 999999):06d}"
            create_otp(msv, code, ttl_minutes=10)
            subject = "Mã xác thực đăng nhập khảo sát (OTP)"
            body = f"Xin chào {stu['name']},\n\nMã xác thực (OTP) của bạn là: {code}\nHiệu lực: 10 phút.\nNếu bạn không yêu cầu, xin bỏ qua email này.\n\nTrân trọng."
            ok = send_email_code(email, subject, body)
            if ok:
                st.session_state["otp_ready_for"] = msv
                st.success("✅ Đã gửi mã OTP vào email của bạn. Vui lòng kiểm tra hộp thư (cả Spam/Junk).")

# ---------- Step 2: Verify OTP ----------
otp_ready_for = st.session_state.get("otp_ready_for")
if otp_ready_for:
    with st.form("otp_form"):
        st.subheader("Nhập mã OTP")
        otp = st.text_input("Mã 6 chữ số", max_chars=6)
        verify_btn = st.form_submit_button("Xác thực")

    if verify_btn:
        if verify_otp(otp_ready_for, otp.strip()):
            st.session_state["auth_msv"] = otp_ready_for
            st.success("✅ Xác thực thành công.")
        else:
            st.error("❌ Mã OTP không hợp lệ hoặc đã hết hạn.")

auth_msv = st.session_state.get("auth_msv")
if not auth_msv:
    st.stop()

# ---------- After auth: survey ----------
stu = get_student(auth_msv)
if stu and stu.get("completed"):
    st.success(f"🎉 Điểm thi vấn đáp của bạn: **{stu['score']}**")
    st.info("Bạn đã hoàn tất khảo sát. Dưới đây là câu trả lời của bạn (không thể chỉnh sửa).")

    data = get_student_responses(auth_msv)
    current_group = None
    for item in data:
        if item["group_name"] != current_group:
            st.markdown(f"### {item['group_name']}")
            current_group = item["group_name"]
        if item["qtype"] == "slider":
            label_map = {1: item["low_label"], 2: item["mid_label"], 3: item["high_label"]}
            val = item["value_int"]
            display = label_map.get(val, "-") if val is not None else "-"
            st.markdown(f"**{item['order_no']}. {item['text']}**")
            st.caption(f"Đáp án của bạn: {display} (mức {val if val is not None else '-'})")
        else:
            txt = item["value_text"] or ""
            st.markdown(f"**{item['order_no']}. {item['text']}**")
            st.text_area("", value=txt, height=100, disabled=True, key=f"ro_{item['question_id']}")
    st.stop()

questions = list_questions()

st.divider()
st.subheader("Bảng câu hỏi")
st.caption("• Câu hỏi đóng dùng **Slider 3 mức**. • Câu hỏi mở dùng ô nhập văn bản. • Hoàn thành **tất cả** câu hỏi.")

# Hiển thị câu hỏi ngoài Form để realtime
answers = {}
current_group = None

for q in questions:
    if q["group_name"] != current_group:
        st.markdown(f"### {q['group_name']}")
        current_group = q["group_name"]

    if q["qtype"] == "slider":
        low, mid, high = q["low_label"], q["mid_label"], q["high_label"]
        label_map = {1: low, 2: mid, 3: high}

        slider_key = f"slider_{q['id']}"
        st.markdown(f"**Thang đo:** 1 = {low} | 2 = {mid} | 3 = {high}")
        # Dùng default từ session_state nếu có, KHÔNG ghi trực tiếp vào session để tránh cảnh báo
        default_val = st.session_state.get(slider_key, 2)
        val = st.slider(
            f"{q['order_no']}. {q['text']}",
            min_value=1, max_value=3, value=default_val, step=1,
            help=f"1 = {low} | 2 = {mid} | 3 = {high}", key=slider_key
        )
        selected_label = label_map.get(val, f"Giá trị {val}")
        st.caption(f"Bạn chọn: **{selected_label}** (mức {val})")
        answers[q["id"]] = {"value_int": val, "value_text": None}
    else:
        txt_key = f"open_{q['id']}"
        txt = st.text_area(f"{q['order_no']}. {q['text']}", height=100, key=txt_key, max_chars=300)
        answers[q["id"]] = {"value_int": None, "value_text": txt}

submit = st.button("Gửi bài khảo sát")

if submit:
    missing = []
    for q in questions:
        a = answers.get(q["id"])
        if q["qtype"] == "slider":
            if a["value_int"] is None:
                missing.append(q["order_no"])
        else:
            if not (a["value_text"] and a["value_text"].strip()):
                missing.append(q["order_no"])
    if missing:
        st.error(f"❌ Bạn chưa trả lời đầy đủ các câu: {', '.join(map(str, missing))}")
        st.stop()

    payload = [
        {"question_id": qid, "value_int": v["value_int"], "value_text": v["value_text"]}
        for qid, v in answers.items()
    ]
    save_responses(auth_msv, payload)
    mark_completed(auth_msv)

    stu2 = get_student(auth_msv)
    st.success("✅ Đã ghi nhận phản hồi. Cảm ơn bạn!")
    st.balloons()
    st.info(f"🎉 Điểm thi vấn đáp của bạn: **{stu2['score']}**")
