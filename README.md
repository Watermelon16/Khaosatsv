# Hệ thống Web Khảo sát Sinh viên (Streamlit) — Bản OTP qua Email

## Cách chạy nhanh
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

- Tài khoản **Admin (test)**: 
  - Username: `admin`
  - Password: `xxxx`
- Import file Excel mẫu `sample_students.xlsx` (4 cột: Mã sinh viên, Email, Họ và tên, Điểm thi vấn đáp).

## Cấu hình Email OTP (mã truy cập 1 lần)
Ứng dụng sử dụng SMTP để gửi mã OTP. Tạo file `.streamlit/secrets.toml` cùng cấp với `app.py`:

```toml
[email]
host = "smtp.gmail.com"
port = 587
user = "your_account@gmail.com"
password = "your_app_password"  # App Password (không phải mật khẩu Gmail thường)
use_tls = true
from_name = "Bộ phận Khảo sát"
dev_mode = false  # true để hiện mã OTP trên màn hình cho môi trường phát triển
```

> Gmail: bật 2FA và tạo **App Password**. Hoặc dùng SMTP của trường/khoa.

## Tính năng
- Sinh viên đăng nhập bằng **MSV + Email** → nhận **OTP 6 chữ số** gửi qua email (hết hạn 10 phút).  
- **Hoàn thành khảo sát** mới được xem điểm.  
- Slider 3 mức với nhãn tuỳ chỉnh.  
- Admin chỉnh sửa danh sách câu hỏi & nhãn thang đo.  
- Dashboard biểu đồ + WordCloud.  
- Import/Export dữ liệu Excel/CSV.
