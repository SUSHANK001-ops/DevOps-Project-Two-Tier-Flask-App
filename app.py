import os
from contextlib import closing

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "local-development-key")


def database_config():
    return {
        "host": os.environ.get("MYSQL_HOST", "localhost"),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", "root"),
        "database": os.environ.get("MYSQL_DB", "devops"),
    }


def get_connection():
    return mysql.connector.connect(**database_config())


def initialize_database():
    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        connection.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Please enter a task.", "error")
            return redirect(url_for("index"))

        try:
            with closing(get_connection()) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
                connection.commit()
        except Error:
            app.logger.exception("Unable to save task")
            flash("The database is unavailable. Please try again.", "error")
        else:
            flash("Task added.", "success")
        return redirect(url_for("index"))

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    "SELECT id, title, created_at FROM tasks ORDER BY created_at DESC, id DESC"
                )
                tasks = cursor.fetchall()
    except Error:
        app.logger.exception("Unable to load tasks")
        return render_template("index.html", tasks=[], database_error=True), 503

    return render_template("index.html", tasks=tasks, database_error=False)


@app.post("/tasks/<int:task_id>/delete")
def delete_task(task_id):
    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            connection.commit()
    except Error:
        app.logger.exception("Unable to delete task %s", task_id)
        flash("The database is unavailable. Please try again.", "error")
    else:
        flash("Task deleted.", "success")
    return redirect(url_for("index"))


@app.get("/health")
def health():
    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Error:
        app.logger.exception("Health check failed")
        return {"status": "unhealthy"}, 503
    return {"status": "healthy"}


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
