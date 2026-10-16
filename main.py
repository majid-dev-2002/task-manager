from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Task Manager API", version="1.0")


def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row  
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


init_db()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool

    class Config:
        orm_mode = True


@app.get("/tasks", response_model=List[Task])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(task) for task in tasks]


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)",
        (task.title, task.description, False)
    )
    conn.commit()
    task_id = cursor.lastrowid
    new_task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(new_task)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="کار مورد نظر پیدا نشد!")
    
    title = task_update.title if task_update.title is not None else task["title"]
    description = task_update.description if task_update.description is not None else task["description"]
    completed = task_update.completed if task_update.completed is not None else task["completed"]

    conn.execute(
        "UPDATE tasks SET title = ?, description = ?, completed = ? WHERE id = ?",
        (title, description, completed, task_id)
    )
    conn.commit()
    updated_task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(updated_task)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="کار مورد نظر پیدا نشد!")
    
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "کار با موفقیت حذف شد."}