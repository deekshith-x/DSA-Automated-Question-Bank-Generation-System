import os
import sqlite3
from contextlib import closing

from config import DB_PATH


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with closing(get_db_connection()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_type TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                keywords TEXT,
                source_file TEXT,
                quality_score INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)")
        conn.commit()


def create_user(username, password_hash):
    with closing(get_db_connection()) as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def fetch_user_by_username(username):
    with closing(get_db_connection()) as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def insert_question(question_data):
    with closing(get_db_connection()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO questions (question, answer, question_type, topic, difficulty, keywords, source_file, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question_data['question'],
                question_data['answer'],
                question_data['question_type'],
                question_data['topic'],
                question_data['difficulty'],
                ', '.join(question_data.get('keywords', [])),
                question_data.get('source_file', 'uploaded.pdf'),
                question_data.get('quality_score', 0),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def fetch_all_questions():
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            """
            SELECT id, question, answer, question_type AS question_type, topic, difficulty, keywords, source_file, quality_score, created_at
            FROM questions
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def fetch_question_by_id(question_id):
    with closing(get_db_connection()) as conn:
        row = conn.execute(
            """
            SELECT id, question, answer, question_type AS question_type, topic, difficulty, keywords, source_file, quality_score, created_at
            FROM questions WHERE id = ?
            """,
            (question_id,),
        ).fetchone()
        return dict(row) if row else None


def fetch_question_stats():
    with closing(get_db_connection()) as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM questions").fetchone()['count']
        topics = conn.execute("SELECT COUNT(DISTINCT topic) AS count FROM questions").fetchone()['count']
        easy = conn.execute("SELECT COUNT(*) AS count FROM questions WHERE difficulty = 'Easy'").fetchone()['count']
        medium = conn.execute("SELECT COUNT(*) AS count FROM questions WHERE difficulty = 'Medium'").fetchone()['count']
        hard = conn.execute("SELECT COUNT(*) AS count FROM questions WHERE difficulty = 'Hard'").fetchone()['count']
        return {
            'total_questions': total,
            'topics': topics,
            'easy': easy,
            'medium': medium,
            'hard': hard,
        }


def search_questions(term=None, topic=None, difficulty=None, question_type=None, keyword=None):
    conditions = []
    params = []

    if term:
        conditions.append("(question LIKE ? OR answer LIKE ? OR source_file LIKE ?)")
        like_term = f"%{term}%"
        params.extend([like_term, like_term, like_term])

    if topic:
        conditions.append("topic = ?")
        params.append(topic)

    if difficulty:
        conditions.append("difficulty = ?")
        params.append(difficulty)

    if question_type:
        conditions.append("question_type = ?")
        params.append(question_type)

    if keyword:
        conditions.append("keywords LIKE ?")
        params.append(f"%{keyword}%")

    base_query = "SELECT id, question, answer, question_type AS question_type, topic, difficulty, keywords, source_file, quality_score, created_at FROM questions"
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    base_query += " ORDER BY created_at DESC, id DESC"

    with closing(get_db_connection()) as conn:
        rows = conn.execute(base_query, params).fetchall()
        return [dict(row) for row in rows]
