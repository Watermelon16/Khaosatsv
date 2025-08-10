import streamlit as st
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Import các module khác sau khi set_page_config
import pandas as pd
import re
import unicodedata as ud
import matplotlib as mpl
import math
import matplotlib.pyplot as plt
from db import init_db, list_questions, fetch_results, get_student

# Kiểm tra wordcloud
try:
    from wordcloud import WordCloud, STOPWORDS
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

init_db()

# Quyền xem dashboard nghiêm ngặt:
# - Admin đăng nhập luôn xem được
# - Sinh viên: phải đăng nhập (auth_msv tồn tại) và đã hoàn thành khảo sát
is_admin = bool(st.session_state.get("admin_auth"))
if not is_admin:
    auth_msv = st.session_state.get("auth_msv")
    if not auth_msv:
        st.error("Bạn chưa đăng nhập. Vui lòng vào tab Sinh viên để đăng nhập (OTP).")
        st.stop()
    stu = get_student(auth_msv)
    if not (stu and stu.get("completed")):
        st.error("Bạn chưa hoàn thành khảo sát nên chưa thể xem Dashboard.")
        st.stop()

# Hiển thị thông báo về wordcloud nếu cần
if not WORDCLOUD_AVAILABLE:
    st.warning("⚠️ Module wordcloud chưa được cài đặt. Phần WordCloud sẽ bị tắt.")

# CSS để cải thiện giao diện
st.markdown("""
<style>
    .dashboard-title {
        font-size: 1.5rem !important;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.1rem !important;
        font-weight: 500;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ecf0f1;
    }
    .question-text {
        font-size: 0.9rem !important;
        font-weight: 500;
        color: #34495e;
        margin-bottom: 0.5rem;
    }
    .chart-caption {
        font-size: 0.75rem !important;
        color: #7f8c8d;
        font-style: italic;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
    }
    .metric-box h3 {
        font-size: 0.9rem !important;
        margin: 0 0 0.3rem 0;
    }
    .metric-box h2 {
        font-size: 1.5rem !important;
        margin: 0;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="dashboard-title">📊 Dashboard</h1>', unsafe_allow_html=True)

# Giảm font mặc định cho toàn bộ biểu đồ
mpl.rcParams.update({
    'font.size': 6,
    'axes.titlesize': 6,
    'axes.labelsize': 6,
    'xtick.labelsize': 5,
    'ytick.labelsize': 5,
})

results = fetch_results()
if not results:
    st.info("📝 Chưa có dữ liệu phản hồi.")
    st.stop()

# Chặn sinh viên chưa hoàn thành xem dashboard nếu chạy qua page sinh viên
st.caption("Dashboard chỉ để xem tổng hợp. Sinh viên cần hoàn thành khảo sát để xem điểm trong trang Sinh viên.")

qs = list_questions()
qs_by_id = {q["id"]: q for q in qs}

df = pd.DataFrame(results)

# Thống kê tổng quan
total_responses = len(df['msv'].unique())
total_questions = len(qs)
completed_surveys = len(df[df['question_id'] == qs[0]['id']])

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-box">
        <h3>👥 Tổng sinh viên</h3>
        <h2>{total_responses}</h2>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-box">
        <h3>❓ Tổng câu hỏi</h3>
        <h2>{total_questions}</h2>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-box">
        <h3>✅ Hoàn thành</h3>
        <h2>{completed_surveys}</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<h2 class="section-header">📈 Phân Phối Câu Trả Lời (Slider)</h2>', unsafe_allow_html=True)

for q in [q for q in qs if q["qtype"] == "slider"]:
    sub = df[df["question_id"] == q["id"]]
    counts = sub["value_int"].value_counts().sort_index()
    label_map = {1: q["low_label"], 2: q["mid_label"], 3: q["high_label"]}
    labels = [label_map.get(k, str(k)) for k in [1,2,3]]
    values = [int(counts.get(k, 0)) for k in [1,2,3]]

    st.markdown(f'<p class="question-text"><strong>{q["order_no"]}. {q["text"]}</strong></p>', unsafe_allow_html=True)
    
    # Tạo biểu đồ nhỏ gọn hơn - giảm thêm 50% chiều ngang
    fig, ax = plt.subplots(figsize=(2.4, 1.2), dpi=110)
    bars = ax.bar(labels, values, color=['#e74c3c', '#f39c12', '#27ae60'], alpha=0.8)
    
    # Thêm số liệu trên cột
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{value}', ha='center', va='bottom', fontweight='bold', fontsize=7)
    
    ax.set_xlabel("Mức đánh giá", fontsize=5)
    ax.set_ylabel("Số lượng", fontsize=5)
    ax.set_title("", fontsize=6)
    ax.grid(axis='y', alpha=0.3)
    ax.tick_params(axis='both', labelsize=5)
    plt.tight_layout()
    
    st.pyplot(fig, use_container_width=False)
    st.markdown(f'<p class="chart-caption">Thang đo: 1 = {q["low_label"]} | 2 = {q["mid_label"]} | 3 = {q["high_label"]}</p>', unsafe_allow_html=True)
    st.divider()

if WORDCLOUD_AVAILABLE:
    st.markdown('<h2 class="section-header">☁️ WordCloud (Câu Hỏi Mở)</h2>', unsafe_allow_html=True)
    vn_stop = set([
        "và","là","của","cho","các","những","được","trong","khi","đã","với","tôi",
        "cần","rất","thì","nên","có","không","cũng","như","đến","để","một","mọi",
        "vì","ở","ra","này","kia","đó","đang","sẽ","đi","bị","từ","học","môn"
    ])
    stopwords = STOPWORDS.union(vn_stop)

    for q in [q for q in qs if q["qtype"] == "open"]:
        sub = df[(df["question_id"] == q["id"]) & (df["value_text"].notnull())]
        raw_texts = [str(x) for x in sub["value_text"].tolist() if str(x).strip()]
        if not raw_texts:
            continue

        # Gom theo cụm câu trả lời giống nhau (bỏ khoảng trắng thừa và dấu câu cuối)
        canon_to_display: dict[str, tuple[str, int]] = {}
        for t in raw_texts:
            display = re.sub(r"\s+", " ", t.strip())
            # Bỏ ký tự phân tách/dấu câu ở cuối (Unicode), tránh regex \p; dùng unicodedata
            tmp = display
            while tmp and (ud.category(tmp[-1]).startswith('P') or ud.category(tmp[-1]).startswith('Z')):
                tmp = tmp[:-1]
            canonical = tmp.lower()
            if canonical in canon_to_display:
                old_disp, cnt = canon_to_display[canonical]
                canon_to_display[canonical] = (old_disp, cnt + 1)
            else:
                canon_to_display[canonical] = (display, 1)

        # Tạo frequencies theo cụm câu trả lời (mỗi câu là một token)
        frequencies = {disp: cnt for disp, cnt in canon_to_display.values()}

        try:
            # Tăng kích thước chữ theo tần suất, nhưng vẫn giữ tổng thể gọn
            max_count = max(frequencies.values())
            # Tính max_font_size động: cơ sở 18, cộng thêm 6px cho mỗi lần lặp (tối đa 60)
            dynamic_max_font = min(60, 18 + max_count * 6)
            wc = WordCloud(
                width=160,
                height=60,
                background_color="white",
                collocations=False,  # giữ nguyên cụm, không tách bigram
                max_words=30,
                max_font_size=int(dynamic_max_font),
                min_font_size=6,
                prefer_horizontal=1,
                margin=0,
                relative_scaling=0.5,
            ).generate_from_frequencies(frequencies)

            st.markdown(f'<p class="question-text"><strong>{q["order_no"]}. {q["text"]}</strong></p>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(2.0, 0.9), dpi=120)
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=False)

            st.markdown(f'<p class="chart-caption">Số câu trả lời: {len(raw_texts)} · Số cụm khác nhau: {len(frequencies)}</p>', unsafe_allow_html=True)
            st.divider()
        except Exception as e:
            st.error(f"Lỗi tạo WordCloud cho câu hỏi {q['order_no']}: {e}")
else:
    st.markdown('<h2 class="section-header">📝 Câu Hỏi Mở (WordCloud Tạm Thời Bị Tắt)</h2>', unsafe_allow_html=True)
    for q in [q for q in qs if q["qtype"] == "open"]:
        sub = df[(df["question_id"] == q["id"]) & (df["value_text"].notnull())]
        texts = [str(x) for x in sub["value_text"].tolist() if str(x).strip()]
        if texts:
            st.markdown(f'<p class="question-text"><strong>{q["order_no"]}. {q["text"]}</strong></p>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-box"><strong>Số câu trả lời:</strong> {len(texts)}</div>', unsafe_allow_html=True)
            st.divider()
