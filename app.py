from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import psycopg


DB_CONFIG = {
    "host": "db",
    "dbname": "notesdb",
    "user": "notesuser",
    "password": "secret",
}


def get_connection():
    return psycopg.connect(**DB_CONFIG)


def setup_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL
                )
            """)
        conn.commit()


def get_notes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content FROM notes ORDER BY id")
            return cur.fetchall()


def add_note(content):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notes (content) VALUES (%s)",
                (content,)
            )
        conn.commit()


def delete_note(note_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM notes WHERE id = %s",
                (note_id,)
            )
        conn.commit()


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        notes = get_notes()

        html = """
        <html>
            <head>
                <title>Mini Notes</title>
            </head>

            <body>
                <h1>Mini Notes</h1>

                <form method="POST">
                    <input
                        type="text"
                        name="note"
                        placeholder="Write a note"
                        required
                    >
                    <button type="submit">Add</button>
                </form>

                <h2>Notes</h2>
                <ul>
        """

        for note_id, content in notes:
            html += f"""
                    <li>
                        {content}
                        <form method="POST" style="display:inline;">
                            <input type="hidden" name="delete" value="{note_id}">
                            <button type="submit">Delete</button>
                        </form>
                    </li>
            """

        html += """
                </ul>
            </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)

        if "note" in data:
            content = data["note"][0].strip()

            if content:
                add_note(content)

        elif "delete" in data:
            note_id = int(data["delete"][0])
            delete_note(note_id)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


if __name__ == "__main__":
    setup_database()

    server = HTTPServer(("0.0.0.0", 5000), Handler)

    print("Mini Notes running on port 5000")

    server.serve_forever()
