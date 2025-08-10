import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

DB_PATH = Path("survey.db")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            msv TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            score REAL,
            completed INTEGER DEFAULT 0,
            completed_at TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            order_no INTEGER,
            text TEXT,
            qtype TEXT CHECK(qtype IN ('slider','open')) NOT NULL,
            low_label TEXT,
            mid_label TEXT,
            high_label TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msv TEXT,
            question_id INTEGER,
            value_int INTEGER,
            value_text TEXT,
            created_at TEXT,
            FOREIGN KEY(msv) REFERENCES students(msv),
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msv TEXT,
            code_hash TEXT,
            expires_at TEXT,
            created_at TEXT,
            used INTEGER DEFAULT 0
        )
        """)
    seed_questions_if_empty()

def _default_questions_data():
    return [
        # Nhóm 1 – Thực tập tại đơn vị
        ("Nhóm 1 – Thực tập tại đơn vị", 1,
         "Môi trường làm việc thực tế có đúng như em mong đợi?",
         "slider", "Không", "Tương đối", "Rất đúng"),
        ("Nhóm 1 – Thực tập tại đơn vị", 2,
         "Em đã học hỏi được nhiều kiến thức/kỹ năng thực tế?",
         "slider", "Ít", "Trung bình", "Nhiều"),
        ("Nhóm 1 – Thực tập tại đơn vị", 3,
         "Mức độ hỗ trợ của đơn vị thực tập dành cho em?",
         "slider", "Thấp", "Trung bình", "Cao"),
        ("Nhóm 1 – Thực tập tại đơn vị", 4,
         "Khó khăn lớn nhất em gặp trong thời gian thực tập và đề xuất cải thiện?",
         "open", None, None, None),

        # Nhóm 2 – Khóa BIM–Revit và 2 chuyên đề ở trường
        ("Nhóm 2 – Khóa BIM–Revit và 2 chuyên đề ở trường", 5,
         "Khối lượng và thời gian học BIM–Revit 4 buổi có hợp lý?",
         "slider", "Không", "Tạm được", "Rất hợp lý"),
        ("Nhóm 2 – Khóa BIM–Revit và 2 chuyên đề ở trường", 6,
         "Mức độ khó của chuyên đề kỹ thuật 1 (tự tìm hiểu BIM & Revit)?",
         "slider", "Dễ", "Vừa", "Khó"),
        ("Nhóm 2 – Khóa BIM–Revit và 2 chuyên đề ở trường", 7,
         "Mức độ khó của chuyên đề kỹ thuật 2 (mô hình hóa công trình thủy lợi)?",
         "slider", "Dễ", "Vừa", "Khó"),
        ("Nhóm 2 – Khóa BIM–Revit và 2 chuyên đề ở trường", 8,
         "Điều bạn mong muốn cải thiện về khóa học BIM–Revit?",
         "open", None, None, None),

        # Nhóm 3 – Tổng thể học phần thực tập tốt nghiệp
        ("Nhóm 3 – Tổng thể học phần thực tập tốt nghiệp", 9,
         "Qua học phần này, em đã học được những kiến thức hoặc kỹ năng gì?",
         "open", None, None, None),
        ("Nhóm 3 – Tổng thể học phần thực tập tốt nghiệp", 10,
         "Điều em mong muốn cải thiện nhất ở học phần này là gì?",
         "open", None, None, None),

        # Nhóm 4 – Liên quan nguyện vọng đăng ký đồ án tốt nghiệp
        ("Nhóm 4 – Nguyện vọng đăng ký đồ án tốt nghiệp", 11,
         "Nguyện vọng đăng ký đồ án tốt nghiệp sắp tới của em theo bộ môn nào?",
         "slider", "BM CT Biển và ĐT", "BM Thủy công", "BM Thủy điện và NLTT"),
    ]

def seed_questions_if_empty():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS n FROM questions")
        if c.fetchone()["n"] > 0:
            return
        data = _default_questions_data()
        c.executemany("""
            INSERT INTO questions (group_name, order_no, text, qtype, low_label, mid_label, high_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)

def reset_questions_to_new_default():
    with get_conn() as conn:
        c = conn.cursor()
        # Xóa responses trước để tránh ràng buộc
        c.execute("DELETE FROM responses")
        c.execute("DELETE FROM questions")
        data = _default_questions_data()
        c.executemany(
            """
            INSERT INTO questions (group_name, order_no, text, qtype, low_label, mid_label, high_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )

def upsert_students(rows):
    with get_conn() as conn:
        c = conn.cursor()
        for r in rows:
            c.execute("""
            INSERT INTO students (msv, email, name, score, completed, completed_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT completed FROM students WHERE msv=?), 0),
                    COALESCE((SELECT completed_at FROM students WHERE msv=?), NULL))
            ON CONFLICT(msv) DO UPDATE SET
                email=excluded.email,
                name=excluded.name,
                score=excluded.score
            """, (r["msv"], r["email"], r["name"], r["score"], r["msv"], r["msv"]))

def get_student(msv):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE msv=?", (msv,))
        row = c.fetchone()
        return dict(row) if row else None

def mark_completed(msv):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE students SET completed=1, completed_at=? WHERE msv=?", 
                  (datetime.utcnow().isoformat(), msv))

def list_questions():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM questions ORDER BY order_no ASC")
        return [dict(r) for r in c.fetchall()]

def update_question(qid, text=None, low=None, mid=None, high=None, group_name=None, qtype=None):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM questions WHERE id=?", (qid,))
        if not c.fetchone():
            return
        # Validate qtype
        if qtype not in (None, 'slider', 'open'):
            qtype = None
        c.execute(
            """
            UPDATE questions 
            SET text=COALESCE(?, text),
                low_label=COALESCE(?, low_label),
                mid_label=COALESCE(?, mid_label),
                high_label=COALESCE(?, high_label),
                group_name=COALESCE(?, group_name),
                qtype=COALESCE(?, qtype)
            WHERE id=?
            """,
            (text, low, mid, high, group_name, qtype, qid),
        )

def create_question(text: str, group_name: str, qtype: str, low: str | None = None,
                    mid: str | None = None, high: str | None = None, order_no: int | None = None) -> int:
    if qtype not in ('slider', 'open'):
        raise ValueError("qtype must be 'slider' or 'open'")
    with get_conn() as conn:
        c = conn.cursor()
        if order_no is None:
            c.execute("SELECT COALESCE(MAX(order_no), 0) + 1 FROM questions")
            order_no = int(c.fetchone()[0])
        c.execute(
            """
            INSERT INTO questions (group_name, order_no, text, qtype, low_label, mid_label, high_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (group_name, order_no, text, qtype, low, mid, high),
        )
        return c.lastrowid

def delete_question(qid: int) -> None:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM questions WHERE id=?", (qid,))

def save_responses(msv, response_list):
    with get_conn() as conn:
        c = conn.cursor()
        for r in response_list:
            c.execute("""
            INSERT INTO responses (msv, question_id, value_int, value_text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (msv, r.get("question_id"), r.get("value_int"), r.get("value_text"),
                  datetime.utcnow().isoformat()))

def fetch_results():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT q.id as question_id, q.text as question_text, q.qtype, 
               q.low_label, q.mid_label, q.high_label,
               r.msv, r.value_int, r.value_text
        FROM responses r
        JOIN questions q ON q.id = r.question_id
        """)
        return [dict(r) for r in c.fetchall()]

def list_students():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM students ORDER BY msv ASC")
        return [dict(r) for r in c.fetchall()]

def update_student(msv: str, email: str | None = None, name: str | None = None, score: float | None = None):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE students SET
                email=COALESCE(?, email),
                name=COALESCE(?, name),
                score=COALESCE(?, score)
            WHERE msv=?
            """,
            (email, name, score, msv),
        )

def delete_student(msv: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM responses WHERE msv=?", (msv,))
        c.execute("DELETE FROM students WHERE msv=?", (msv,))

def export_responses_as_rows():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT r.id, r.msv, s.name, s.email, s.score, q.id as question_id, q.text as question_text,
               q.qtype, r.value_int, r.value_text, r.created_at
        FROM responses r
        JOIN questions q ON q.id = r.question_id
        JOIN students s ON s.msv = r.msv
        ORDER BY r.id ASC
        """)
        return [dict(r) for r in c.fetchall()]

def reset_responses_and_completion():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM responses")
        c.execute("UPDATE students SET completed=0, completed_at=NULL")

def get_student_responses(msv: str):
    """Return list of questions with the student's answers (if any), ordered by order_no."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT q.id as question_id,
                   q.group_name, q.order_no, q.text, q.qtype,
                   q.low_label, q.mid_label, q.high_label,
                   r.value_int, r.value_text, r.created_at
            FROM questions q
            LEFT JOIN responses r
              ON r.question_id = q.id AND r.msv = ?
            ORDER BY q.order_no ASC
            """,
            (msv,),
        )
        return [dict(r) for r in c.fetchall()]

# ---------- OTP helpers ----------
def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def can_request_otp(msv: str, cooldown_sec: int = 60) -> bool:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT created_at FROM otps WHERE msv=? ORDER BY id DESC LIMIT 1", (msv,))
        row = c.fetchone()
        if not row: 
            return True
        last = datetime.fromisoformat(row["created_at"])
        return (datetime.utcnow() - last).total_seconds() >= cooldown_sec

def create_otp(msv: str, code: str, ttl_minutes: int = 10):
    with get_conn() as conn:
        c = conn.cursor()
        code_hash = _hash_code(code)
        expires_at = (datetime.utcnow() + timedelta(minutes=ttl_minutes)).isoformat()
        c.execute("""
        INSERT INTO otps (msv, code_hash, expires_at, created_at, used)
        VALUES (?, ?, ?, ?, 0)
        """, (msv, code_hash, expires_at, datetime.utcnow().isoformat()))

def verify_otp(msv: str, code: str) -> bool:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT id, code_hash, expires_at, used FROM otps 
        WHERE msv=? ORDER BY id DESC LIMIT 1
        """, (msv,))
        row = c.fetchone()
        if not row:
            return False
        if row["used"] == 1:
            return False
        if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
            return False
        if _hash_code(code) != row["code_hash"]:
            return False
        c.execute("UPDATE otps SET used=1 WHERE id=?", (row["id"],))
        return True
