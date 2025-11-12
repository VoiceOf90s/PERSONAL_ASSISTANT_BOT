import sqlite3, os, datetime
DB_PATH = "data/bot.db"
os.makedirs("data", exist_ok=True)

def conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                city TEXT
            );
            CREATE TABLE IF NOT EXISTS reminders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                remind_at TEXT
            );
            -- Индексы для оптимизации запросов
            CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
            CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
        """)

def save_user(uid, username, full_name):
    with conn() as c:
        c.execute("REPLACE INTO users(id, username, full_name) VALUES(?,?,?)",
                  (uid, username, full_name))

def get_user(uid):
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def get_all_users():
    with conn() as c:
        return c.execute("SELECT * FROM users").fetchall()

def set_city(uid, city):
    with conn() as c:
        # Создаем пользователя если его нет
        c.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (uid,))
        c.execute("UPDATE users SET city=? WHERE id=?", (city, uid))

def add_reminder(uid, text, when: datetime.datetime):
    with conn() as c:
        c.execute("INSERT INTO reminders(user_id, text, remind_at) VALUES(?,?,?)",
                  (uid, text, when.strftime("%Y-%m-%d %H:%M")))

def get_active_reminders(uid=None):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    sql = "SELECT id, user_id, text, remind_at FROM reminders WHERE remind_at>=?"
    params = (now,)
    if uid:
        sql += " AND user_id=?"
        params += (uid,)
    with conn() as c:
        return c.execute(sql, params).fetchall()

def get_reminder_owner(rid):
    """Получить user_id владельца напоминания"""
    with conn() as c:
        row = c.execute("SELECT user_id FROM reminders WHERE id=?", (rid,)).fetchone()
        return row[0] if row else None

def del_reminder(rid, user_id=None):
    """Удалить напоминание. Если указан user_id, проверяется владелец"""
    with conn() as c:
        if user_id:
            # Удаляем только если пользователь является владельцем
            c.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (rid, user_id))
            return c.rowcount > 0
        else:
            c.execute("DELETE FROM reminders WHERE id=?", (rid,))
            return c.rowcount > 0