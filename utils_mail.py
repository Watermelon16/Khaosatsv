import smtplib, ssl
from email.mime.text import MIMEText
from email.utils import formataddr
import streamlit as st

def get_email_conf():
    try:
        cfg = st.secrets.get("email", {})
    except Exception:
        # Fallback khi không có secrets.toml
        cfg = {}
    
    return {
        "host": cfg.get("host"),
        "port": int(cfg.get("port", 587)),
        "user": cfg.get("user"),
        "password": cfg.get("password"),
        "use_tls": bool(cfg.get("use_tls", True)),
        "from_name": cfg.get("from_name", "Survey System"),
        "dev_mode": bool(cfg.get("dev_mode", True)),  # Mặc định bật dev mode
    }

def send_email_code(to_email: str, subject: str, body: str):
    conf = get_email_conf()
    if conf["dev_mode"]:
        st.warning("DEV MODE đang bật: Không gửi email thật. Nội dung email hiển thị bên dưới.")
        st.code(f"TO: {to_email}\nSUBJECT: {subject}\n\n{body}")
        return True

    if not all([conf["host"], conf["port"], conf["user"], conf["password"]]):
        st.error("Thiếu cấu hình SMTP trong st.secrets['email']. Không thể gửi email.")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((conf["from_name"], conf["user"]))
    msg["To"] = to_email

    try:
        if conf["use_tls"]:
            server = smtplib.SMTP(conf["host"], conf["port"])
            server.starttls(context=ssl.create_default_context())
        else:
            server = smtplib.SMTP_SSL(conf["host"], conf["port"], context=ssl.create_default_context())
        server.login(conf["user"], conf["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Lỗi gửi email: {e}")
        return False
