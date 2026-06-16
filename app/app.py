from flask import Flask, render_template_string, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

def get_db():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        dbname=os.environ.get('DB_NAME', 'blogdb'),
        user=os.environ.get('DB_USER', 'bloguser'),
        password=os.environ.get('DB_PASSWORD'),
        connect_timeout=5
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('SELECT COUNT(*) FROM posts')
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO posts (title, content) VALUES (%s, %s)",
                        ('WELCOME TO SUPER BLOG BROS!', 'Thank you for playing Super Blog Bros! Your quest for knowledge begins here. Collect posts like coins, defeat writer-s-block like a boss, and save the princess of creativity!'))
            cur.execute("INSERT INTO posts (title, content) VALUES (%s, %s)",
                        ('WORLD 1-1: THE CLOUD', 'Deployed on AWS EC2 using Terraform. Every terraform apply is like hitting a question block - you never know what resource pops out. Game Over? Just run terraform destroy!'))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

BASE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}SUPER BLOG BROS{% endblock %}</title>
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
  <style>
    :root {
      --sky: #5C94FC;
      --ground: #C84B0A;
      --brick: #B45309;
      --block: #E77A1E;
      --coin: #FBD000;
      --red: #E52521;
      --green: #3A9413;
      --white: #FCFCFC;
      --black: #000000;
      --dark-blue: #1A1A7E;
      --pipe: #3A9413;
      --cloud: #FCFCFC;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      background-color: var(--sky);
      font-family: 'Press Start 2P', monospace;
      font-size: 8px;
      color: var(--black);
      min-height: 100vh;
      image-rendering: pixelated;
      overflow-x: hidden;
    }

    /* Scrolling clouds */
    .clouds {
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .cloud {
      position: absolute;
      background: var(--white);
      border-radius: 0;
    }

    .cloud-1 { width: 96px; height: 32px; top: 80px; animation: drift 20s linear infinite; }
    .cloud-1::before { content:''; position:absolute; width:64px; height:32px; background:var(--white); top:-16px; left:16px; }
    .cloud-2 { width: 64px; height: 24px; top: 140px; animation: drift 28s linear infinite; animation-delay: -10s; }
    .cloud-2::before { content:''; position:absolute; width:48px; height:24px; background:var(--white); top:-12px; left:8px; }
    .cloud-3 { width: 80px; height: 28px; top: 60px; animation: drift 24s linear infinite; animation-delay: -5s; }
    .cloud-3::before { content:''; position:absolute; width:56px; height:28px; background:var(--white); top:-14px; left:12px; }

    @keyframes drift {
      from { left: -150px; }
      to { left: 110%; }
    }

    /* HUD Header */
    .hud {
      background: var(--dark-blue);
      color: var(--white);
      padding: 16px 24px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 8px solid var(--black);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .hud-brand {
      font-size: 14px;
      color: var(--coin);
      text-decoration: none;
      text-shadow: 4px 4px var(--black);
      letter-spacing: 2px;
    }

    .hud-stats {
      display: flex;
      gap: 24px;
      font-size: 7px;
      color: var(--white);
    }

    .hud-stat span {
      color: var(--coin);
    }

    /* Pixel button */
    .btn {
      display: inline-block;
      background: var(--red);
      color: var(--white);
      padding: 10px 16px;
      font-family: 'Press Start 2P', monospace;
      font-size: 7px;
      text-decoration: none;
      border: none;
      cursor: pointer;
      box-shadow:
        0 6px 0 #8B0000,
        inset 2px 2px 0 rgba(255,255,255,0.3);
      transition: transform 0.1s, box-shadow 0.1s;
      letter-spacing: 1px;
    }

    .btn:hover {
      transform: translateY(3px);
      box-shadow:
        0 3px 0 #8B0000,
        inset 2px 2px 0 rgba(255,255,255,0.3);
    }

    .btn:active {
      transform: translateY(6px);
      box-shadow: none;
    }

    .btn-green {
      background: var(--green);
      box-shadow: 0 6px 0 #1a4a0a, inset 2px 2px 0 rgba(255,255,255,0.3);
    }

    .btn-green:hover {
      box-shadow: 0 3px 0 #1a4a0a, inset 2px 2px 0 rgba(255,255,255,0.3);
    }

    /* Main content area */
    .world {
      position: relative;
      z-index: 1;
      padding: 40px 24px 120px;
      max-width: 860px;
      margin: 0 auto;
    }

    /* World header */
    .world-title {
      text-align: center;
      padding: 32px 0;
    }

    .world-title h1 {
      font-size: 18px;
      color: var(--white);
      text-shadow: 4px 4px var(--dark-blue);
      margin-bottom: 12px;
      letter-spacing: 2px;
    }

    .world-label {
      font-size: 7px;
      color: var(--coin);
      letter-spacing: 3px;
    }

    /* Question blocks row */
    .q-row {
      display: flex;
      justify-content: center;
      gap: 8px;
      margin: 24px 0 40px;
    }

    .q-block {
      width: 40px;
      height: 40px;
      background: var(--block);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      color: var(--coin);
      box-shadow:
        inset -4px -4px 0 rgba(0,0,0,0.4),
        inset 4px 4px 0 rgba(255,255,255,0.3),
        0 0 0 4px var(--black);
      animation: bounce-block 2s ease-in-out infinite;
    }

    .q-block:nth-child(2) { animation-delay: 0.3s; }
    .q-block:nth-child(3) { animation-delay: 0.6s; }
    .q-block:nth-child(4) { animation-delay: 0.9s; }

    @keyframes bounce-block {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }

    /* Post card = brick block style */
    .post-card {
      background: var(--brick);
      border: 4px solid var(--black);
      margin-bottom: 24px;
      box-shadow:
        inset -4px -4px 0 rgba(0,0,0,0.4),
        inset 4px 4px 0 rgba(255,255,255,0.15),
        8px 8px 0 var(--black);
      transition: transform 0.1s;
      position: relative;
      overflow: hidden;
    }

    .post-card:hover {
      transform: translate(-2px, -2px);
      box-shadow:
        inset -4px -4px 0 rgba(0,0,0,0.4),
        inset 4px 4px 0 rgba(255,255,255,0.15),
        10px 10px 0 var(--black);
    }

    .post-card-header {
      background: var(--dark-blue);
      padding: 16px 20px;
      border-bottom: 4px solid var(--black);
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .coin-icon {
      width: 16px;
      height: 16px;
      background: var(--coin);
      border-radius: 50%;
      box-shadow: inset -2px -2px 0 rgba(0,0,0,0.3), inset 2px 2px 0 rgba(255,255,255,0.4);
      flex-shrink: 0;
      animation: spin-coin 3s linear infinite;
    }

    @keyframes spin-coin {
      0%, 100% { transform: scaleX(1); background: var(--coin); }
      25% { transform: scaleX(0.3); background: #a87800; }
      50% { transform: scaleX(1); background: var(--coin); }
      75% { transform: scaleX(0.3); background: #a87800; }
    }

    .post-card h2 {
      font-size: 9px;
      color: var(--coin);
      text-shadow: 2px 2px var(--black);
    }

    .post-card h2 a {
      color: inherit;
      text-decoration: none;
    }

    .post-card h2 a:hover { color: var(--white); }

    .post-card-body {
      padding: 16px 20px;
    }

    .post-meta {
      font-size: 6px;
      color: rgba(252,252,252,0.5);
      margin-bottom: 10px;
      letter-spacing: 1px;
    }

    .post-excerpt {
      font-size: 7px;
      color: var(--white);
      line-height: 2;
    }

    .read-more {
      display: inline-block;
      margin-top: 12px;
      font-size: 7px;
      color: var(--coin);
      text-decoration: none;
      letter-spacing: 1px;
    }

    .read-more::before { content: '> '; }
    .read-more:hover { color: var(--white); }

    /* Single post */
    .post-view {
      background: var(--dark-blue);
      border: 4px solid var(--black);
      padding: 32px;
      box-shadow: 8px 8px 0 var(--black);
    }

    .post-view h1 {
      font-size: 12px;
      color: var(--coin);
      text-shadow: 2px 2px var(--black);
      margin-bottom: 16px;
      line-height: 1.8;
    }

    .post-view .post-meta {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 4px solid rgba(255,255,255,0.1);
    }

    .post-content {
      font-size: 7px;
      color: var(--white);
      line-height: 2.5;
    }

    /* Form */
    .form-box {
      background: var(--dark-blue);
      border: 4px solid var(--black);
      padding: 32px;
      box-shadow: 8px 8px 0 var(--black);
    }

    .form-box h1 {
      font-size: 12px;
      color: var(--coin);
      text-shadow: 2px 2px var(--black);
      margin-bottom: 32px;
    }

    .field { margin-bottom: 24px; }

    label {
      display: block;
      font-size: 7px;
      color: var(--coin);
      margin-bottom: 8px;
      letter-spacing: 1px;
    }

    input, textarea {
      width: 100%;
      background: #000022;
      border: 4px solid var(--black);
      box-shadow: inset 2px 2px 0 rgba(0,0,0,0.5);
      padding: 12px;
      color: var(--white);
      font-family: 'Press Start 2P', monospace;
      font-size: 7px;
      outline: none;
      line-height: 2;
    }

    input:focus, textarea:focus {
      border-color: var(--coin);
    }

    textarea { resize: vertical; min-height: 180px; }

    /* Ground */
    .ground {
      position: fixed;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 48px;
      z-index: 50;
      display: flex;
    }

    .ground-block {
      width: 48px;
      height: 48px;
      flex-shrink: 0;
      background: var(--ground);
      box-shadow:
        inset -4px -4px 0 rgba(0,0,0,0.4),
        inset 4px 4px 0 rgba(255,255,255,0.15),
        0 0 0 2px var(--black);
    }

    /* Back link */
    .back {
      display: inline-block;
      font-size: 7px;
      color: var(--coin);
      text-decoration: none;
      margin-bottom: 24px;
      letter-spacing: 1px;
    }

    .back::before { content: '< '; }
    .back:hover { color: var(--white); }

    /* Empty state */
    .empty {
      text-align: center;
      padding: 48px;
      background: var(--dark-blue);
      border: 4px solid var(--black);
      box-shadow: 8px 8px 0 var(--black);
      color: rgba(252,252,252,0.5);
      font-size: 7px;
      line-height: 2.5;
    }

    /* New post action row */
    .action-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }

    .section-label {
      font-size: 8px;
      color: var(--white);
      text-shadow: 2px 2px var(--dark-blue);
      letter-spacing: 2px;
    }

    /* Pipe decoration */
    .pipe {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 0 auto 32px;
      width: fit-content;
    }

    .pipe-top {
      width: 80px;
      height: 16px;
      background: var(--pipe);
      border: 4px solid var(--black);
      box-shadow: inset -4px -4px 0 rgba(0,0,0,0.4), inset 4px 4px 0 rgba(255,255,255,0.2);
    }

    .pipe-body {
      width: 64px;
      height: 32px;
      background: var(--pipe);
      border: 4px solid var(--black);
      border-top: none;
      box-shadow: inset -4px -4px 0 rgba(0,0,0,0.4), inset 4px 4px 0 rgba(255,255,255,0.2);
    }

    .btn-yellow {
      background: #a87800;
      box-shadow: 0 6px 0 #5a4000, inset 2px 2px 0 rgba(255,255,255,0.3);
    }
    .btn-yellow:hover { box-shadow: 0 3px 0 #5a4000, inset 2px 2px 0 rgba(255,255,255,0.3); }

    .btn-red {
      background: var(--red);
      box-shadow: 0 6px 0 #8B0000, inset 2px 2px 0 rgba(255,255,255,0.3);
    }
    .btn-red:hover { box-shadow: 0 3px 0 #8B0000, inset 2px 2px 0 rgba(255,255,255,0.3); }

    .post-actions {
      display: flex;
      gap: 10px;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 4px solid rgba(255,255,255,0.1);
    }
  </style>
</head>
<body>
  <div class="clouds">
    <div class="cloud cloud-1"></div>
    <div class="cloud cloud-2"></div>
    <div class="cloud cloud-3"></div>
  </div>

  <header class="hud">
    <a href="/" class="hud-brand">SUPER BLOG BROS</a>
    <div class="hud-stats">
      <div class="hud-stat">WORLD <span>1-1</span></div>
      <div class="hud-stat">LIVES <span>&#9829;&#9829;&#9829;</span></div>
    </div>
  </header>

  {% block content %}{% endblock %}

  <div class="ground" id="ground"></div>

  <script>
    const ground = document.getElementById('ground');
    const count = Math.ceil(window.innerWidth / 48) + 1;
    for (let i = 0; i < count; i++) {
      const block = document.createElement('div');
      block.className = 'ground-block';
      ground.appendChild(block);
    }
  </script>
</body>
</html>"""

INDEX = BASE.replace("{% block title %}SUPER BLOG BROS{% endblock %}", "SUPER BLOG BROS").replace(
  "{% block content %}{% endblock %}",
  """<div class="world">
    <div class="world-title">
      <h1>SUPER BLOG BROS</h1>
      <div class="world-label">&#9733; WORLD 1-1 &#9733;</div>
    </div>
    <div class="q-row">
      <div class="q-block">?</div>
      <div class="q-block">?</div>
      <div class="q-block">?</div>
      <div class="q-block">?</div>
    </div>
    <div class="action-row">
      <div class="section-label">LATEST POSTS</div>
      <a href="/new" class="btn">+ NEW POST</a>
    </div>
    {% for p in posts %}
    <div class="post-card">
      <div class="post-card-header">
        <div class="coin-icon"></div>
        <h2><a href="/post/{{ p.id }}">{{ p.title }}</a></h2>
      </div>
      <div class="post-card-body">
        <div class="post-meta">{{ p.created_at }}</div>
        <div class="post-excerpt">{{ p.content[:140] }}{% if p.content|length > 140 %}...{% endif %}</div>
        <a href="/post/{{ p.id }}" class="read-more">READ MORE</a>
      </div>
    </div>
    {% else %}
    <div class="empty">
      <div>NO POSTS FOUND</div>
      <div style="margin-top:16px;">INSERT COIN TO CONTINUE</div>
    </div>
    {% endfor %}
  </div>"""
)

POST = BASE.replace("{% block title %}SUPER BLOG BROS{% endblock %}", "{{ p.title }}").replace(
  "{% block content %}{% endblock %}",
  """<div class="world">
    <a href="/" class="back">BACK TO MAP</a>
    <div class="pipe">
      <div class="pipe-top"></div>
      <div class="pipe-body"></div>
    </div>
    <div class="post-view">
      <h1>{{ p.title }}</h1>
      <div class="post-meta">{{ p.created_at }}</div>
      <div class="post-content">{{ p.content }}</div>
      <div class="post-actions">
        <a href="/edit/{{ p.id }}" class="btn btn-yellow">&#9998; EDIT</a>
        <form method="POST" action="/delete/{{ p.id }}" onsubmit="return confirm('GAME OVER FOR THIS POST?')">
          <button type="submit" class="btn btn-red">&#10006; DELETE</button>
        </form>
      </div>
    </div>
  </div>"""
)

NEW = BASE.replace("{% block title %}SUPER BLOG BROS{% endblock %}", "NEW POST").replace(
  "{% block content %}{% endblock %}",
  """<div class="world">
    <a href="/" class="back">BACK TO MAP</a>
    <div class="form-box">
      <h1>&#9998; NEW POST</h1>
      <form method="POST">
        <div class="field">
          <label>TITLE</label>
          <input name="title" placeholder="ENTER TITLE..." required>
        </div>
        <div class="field">
          <label>CONTENT</label>
          <textarea name="content" placeholder="WRITE YOUR QUEST..." required></textarea>
        </div>
        <button type="submit" class="btn btn-green">PUBLISH &#9733;</button>
      </form>
    </div>
  </div>"""
)

EDIT = BASE.replace("{% block title %}SUPER BLOG BROS{% endblock %}", "EDIT POST").replace(
  "{% block content %}{% endblock %}",
  """<div class="world">
    <a href="/post/{{ p.id }}" class="back">BACK TO POST</a>
    <div class="form-box">
      <h1>&#9998; EDIT POST</h1>
      <form method="POST">
        <div class="field">
          <label>TITLE</label>
          <input name="title" value="{{ p.title }}" required>
        </div>
        <div class="field">
          <label>CONTENT</label>
          <textarea name="content" required>{{ p.content }}</textarea>
        </div>
        <button type="submit" class="btn btn-yellow">SAVE &#9733;</button>
      </form>
    </div>
  </div>"""
)

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(INDEX, posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    p = cur.fetchone()
    cur.close()
    conn.close()
    if not p:
        return 'Post not found', 404
    return render_template_string(POST, p=p)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO posts (title, content) VALUES (%s, %s)',
                    (request.form['title'], request.form['content']))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template_string(NEW)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    p = cur.fetchone()
    cur.close()
    conn.close()
    if not p:
        return 'Post not found', 404
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute('UPDATE posts SET title = %s, content = %s WHERE id = %s',
                    (request.form['title'], request.form['content'], post_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('post', post_id=post_id))
    return render_template_string(EDIT, p=p)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM posts WHERE id = %s', (post_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

init_db()
