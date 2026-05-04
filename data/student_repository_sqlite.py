import sqlite3
from typing import Dict, Any, List, Optional

from .repository_interface import StudentRepositoryInterface


class StudentRepositorySQLite(StudentRepositoryInterface):
    def __init__(self, db_path: str = "students.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            age INTEGER,
            career TEXT,
            semester INTEGER,
            created_at TEXT
        )
        """)
        self.conn.commit()

    def insert(self, student):
        cur = self.conn.cursor()
        # If caller provides an id, insert it explicitly so JSON and SQLite ids stay in sync.
        if student.get("id") is not None:
            cur.execute("""
            INSERT OR REPLACE INTO students(id,name,email,age,career,semester,created_at)
            VALUES(?,?,?,?,?,?,?)
            """, (
                int(student["id"]), student["name"], student["email"], student["age"],
                student["career"], student["semester"], student["created_at"]
            ))
        else:
            cur.execute("""
            INSERT INTO students(name,email,age,career,semester,created_at)
            VALUES(?,?,?,?,?,?)
            """, (
                student["name"], student["email"], student["age"],
                student["career"], student["semester"], student["created_at"]
            ))
        self.conn.commit()

    def get_all(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id,name,email,age,career,semester,created_at FROM students")
        rows = cur.fetchall()
        cols = ["id","name","email","age","career","semester","created_at"]
        return [dict(zip(cols, r)) for r in rows]

    def get_by_id(self, student_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id,name,email,age,career,semester,created_at FROM students WHERE id=?", (student_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = ["id","name","email","age","career","semester","created_at"]
        return dict(zip(cols, row))

    def update(self, student_id, new_data):
        cur = self.conn.cursor()
        fields = []
        values = []
        for k in ("name","email","age","career","semester","created_at"):
            if k in new_data:
                fields.append(f"{k}=?")
                values.append(new_data[k])
        if not fields:
            return False
        # Resolver la fila objetivo: prefiera la fila que ya tiene el email nuevo (si aplica)
        sql = f"UPDATE students SET {', '.join(fields)} WHERE id=?"
        target_id = student_id
        if "email" in new_data:
            cur.execute("SELECT id FROM students WHERE email=?", (new_data["email"],))
            row = cur.fetchone()
            if row:
                # si existe una fila con ese email, actualizar esa fila en lugar de la id provista
                target_id = row[0]

        values_with_target = list(values) + [target_id]
        cur.execute(sql, tuple(values_with_target))
        self.conn.commit()
        return cur.rowcount > 0

    def delete(self, student_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.conn.commit()
        return cur.rowcount > 0
    
    def getultimoingresado(self):
        cur = self.conn.cursor()
        query = "SELECT * FROM students ORDER BY created_at DESC LIMIT 1"
        cur.execute(query)
        ultimo = cur.fetchone()
        return ultimo

    def getmenoredad(self):
        cur = self.conn.cursor()
        query = "SELECT * FROM students ORDER BY age ASC LIMIT 1"
        cur.execute(query)
        student = cur.fetchone()
        return student
    
    def getporcarrera(self, carrera):
        cur = self.conn.cursor()
        query = "SELECT * FROM students WHERE career = ?"
        cur.execute(query, (carrera,))
        students = cur.fetchall()
        return students

    def get_dashboard_data(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*), AVG(age) FROM students")
        total, avg_age = cur.fetchone()
        
        # 2. Conteo por carrera
        cur.execute("SELECT career, COUNT(*) FROM students GROUP BY career")
        career_stats = {row[0]: row[1] for row in cur.fetchall()}
        
        # 3. Conteo por semestre
        cur.execute("SELECT semester, COUNT(*) FROM students GROUP BY semester")
        semester_stats = {f"Semestre {row[0]}": row[1] for row in cur.fetchall()}

        return {
            "total": total,
            "avg_age": round(avg_age, 2) if avg_age else 0,
            "careers": career_stats,
            "semesters": semester_stats
        }
