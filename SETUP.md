# Hướng dẫn cài đặt và cấu hình

## 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

## 2. Cấu hình email (tùy chọn)
Để gửi email OTP thật, chỉnh sửa file `.streamlit/secrets.toml`:

```toml
[email]
host = "smtp.gmail.com"
port = 587
user = "your-email@gmail.com"
password = "your-app-password"  # App password từ Google
use_tls = true
from_name = "Survey System"
dev_mode = false  # Tắt dev mode để gửi email thật
```

**Lưu ý:** 
- Hiện tại `dev_mode = true` - ứng dụng sẽ hiển thị nội dung email thay vì gửi
- Để gửi email thật, cần tạo App Password từ Google Account

## 3. Chạy ứng dụng
```bash
streamlit run app.py
```

## 4. Import danh sách sinh viên
Sử dụng file `sample_students.xlsx` làm mẫu để import danh sách sinh viên.

## 5. Các tính năng đã sửa
✅ **Slider hiển thị kết quả chính xác**: Bây giờ hiển thị đúng mức độ được chọn (real-time)
✅ **WordCloud hoạt động**: Đã cài đặt và xử lý lỗi wordcloud
✅ **Xử lý lỗi email**: Có fallback khi không có cấu hình email
✅ **Giao diện cải thiện**: Hiển thị thang đo rõ ràng hơn
✅ **Dashboard hiện đại**: Giao diện thân thiện, font size phù hợp, biểu đồ đẹp
✅ **Thống kê tổng quan**: Hiển thị số liệu tổng hợp ở đầu dashboard
✅ **Kích thước tối ưu**: Giảm 50% kích thước bar chart và wordcloud để dễ nhìn hơn
✅ **Sửa lỗi session state**: Không còn lỗi khi thay đổi slider

## 6. Lưu ý về Python version
- Ứng dụng chạy với Python 3.10
- Nếu gặp lỗi wordcloud, hãy cài đặt: `py -3.10 -m pip install wordcloud`
- Đảm bảo tất cả dependencies được cài đặt cho đúng Python version
