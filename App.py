import streamlit as st
from db import init_db

st.set_page_config(page_title="Giới thiệu", page_icon="📝", layout="wide")

def main():
    st.title("📝 Giới thiệu")
    st.markdown("""
    **Mục tiêu khảo sát**: Khảo sát này nhằm thu thập ý kiến phản hồi của sinh viên về học phần Thực tập tốt nghiệp, bao gồm trải nghiệm tại đơn vị thực tập, khóa học BIM–Revit và các chuyên đề kỹ thuật, cũng như tổng thể học phần. Kết quả sẽ được dùng để cải thiện nội dung, phương pháp và tổ chức học phần trong các khóa sau.
    
    Sinh viên **phải hoàn tất khảo sát** mới xem được điểm thi vấn đáp.  
    Dùng thanh bên để chọn: **Giới thiệu**, **Sinh viên**, **Admin**, hoặc **Dashboard**.
    """)

    st.info("Lần đầu chạy sẽ tự khởi tạo cơ sở dữ liệu và bộ câu hỏi mặc định.")
    init_db()

if __name__ == "__main__":
    main()
