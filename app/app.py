from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB = '/opt/blog/blog.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute("INSERT OR IGNORE INTO posts (id, title, content) VALUES (1, 'Welcome to My Blog', 'This is my first post deployed on AWS EC2 with Terraform!')")
        conn.execute("INSERT OR IGNORE INTO posts (id, title, content) VALUES (2, 'Flask on AWS', 'Deploying Flask apps on EC2 is easy with Terraform user_data.')")
        conn.commit()

STYLE = """
<style>
  body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
  h1 { color: #333; }
  .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  a { color: #007bff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  input, textarea { width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }
  button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
</style>
"""

INDEX = """<!DOCTYPE html><html><head><title>My Blog</title>{{ style | safe }}</head><body>
  <h1>My Blog</h1><a href="/new"><button>New Post</button></a>
  {% for p in posts %}
  <div class="card">
    <h2><a href="/post/{{ p.id }}">{{ p.title }}</a></h2>
    <small>{{ p.created_at }}</small>
    <p>{{ p.content[:150] }}{% if p.content|length > 150 %}...{% endif %}</p>
  </div>
  {% endfor %}
</body></html>"""

POST = """<!DOCTYPE html><html><head><title>{{ p.title }}</title>{{ style | safe }}</head><body>
  <a href="/">&larr; Back</a>
  <div class="card"><h1>{{ p.title }}</h1><small>{{ p.created_at }}</small><p>{{ p.content }}</p></div>
</body></html>"""

NEW = """<!DOCTYPE html><html><head><title>New Post</title>{{ style | safe }}</head><body>
  <h1>New Post</h1><a href="/">&larr; Back</a>
  <form method="POST">
    <input name="title" placeholder="Title" required>
    <textarea name="content" rows="8" placeholder="Content" required></textarea>
    <button type="submit">Publish</button>
  </form>
</body></html>"""

@app.route('/')
def index():
    with get_db() as conn:
        posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    return render_template_string(INDEX, posts=posts, style=STYLE)

@app.route('/post/<int:post_id>')
def post(post_id):
    with get_db() as conn:
        p = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not p:
        return 'Post not found', 404
    return render_template_string(POST, p=p, style=STYLE)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (request.form['title'], request.form['content']))
            conn.commit()
        return redirect(url_for('index'))
    return render_template_string(NEW, style=STYLE)

init_db()
