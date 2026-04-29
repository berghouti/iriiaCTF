# iriiaCTF Platform

A full CTF (Capture The Flag) learning platform for college students.

## 🚀 Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open browser
http://localhost:5000
```

## 📦 Project Structure

```
ctf_platform/
├── app.py                    # Flask backend + all 10 challenges
├── requirements.txt
├── static/
│   ├── css/style.css         # Full dark hacker UI
│   └── js/main.js            # Flag submission, animations
└── templates/
    ├── base.html             # Layout with navbar
    ├── index.html            # Home / landing page
    ├── learn.html            # CTF explanation + walkthrough
    ├── challenges.html       # Challenge grid with categories
    ├── challenge_detail.html # Individual challenge + submit
    ├── scoreboard.html       # Progress tracker
    └── challenges/           # Interactive challenge pages
        ├── web_inspector.html
        ├── web_cookie.html
        ├── forensics_meta.html
        └── forensics_strings.html
```

## 🏆 Challenges

| ID           | Title              | Category  | Difficulty | Points |
|--------------|--------------------|-----------|------------|--------|
| web_01       | Inspector Gadget   | Web       | Easy       | 50     |
| web_02       | Cookie Monster     | Web       | Medium     | 100    |
| crypto_01    | Caesar's Secret    | Crypto    | Easy       | 50     |
| crypto_02    | Base Basics        | Crypto    | Easy       | 75     |
| crypto_03    | XOR Files          | Crypto    | Medium     | 125    |
| forensics_01 | Metadata Matters   | Forensics | Easy       | 50     |
| forensics_02 | Strings Attached   | Forensics | Medium     | 100    |
| linux_01     | Find the Flag      | Linux     | Easy       | 50     |
| linux_02     | Permission Denied? | Linux     | Easy       | 75     |
| linux_03     | Grep Master        | Linux     | Medium     | 100    |
| linux_04     | Pipe Dream         | Linux     | Medium     | 125    |

**Total: 10 challenges · 725 points**

---

## 🌐 Hosting Options

### Option 1: Render.com (Free, Recommended)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Deploy → Get public URL instantly

### Option 2: Railway.app (Free tier)

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### Option 3: PythonAnywhere (Free)

1. Sign up at pythonanywhere.com
2. Upload files via Files tab
3. Web → Add new web app → Flask
4. Set source to `/home/yourusername/ctf_platform/app.py`

### Option 4: VPS (DigitalOcean / Hetzner)

```bash
# On your server
sudo apt install python3-pip nginx
pip install gunicorn flask

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Use nginx as reverse proxy
# Point domain → server IP
```

---

## 🔧 Adding More Challenges

In `app.py`, add to the `CHALLENGES` dict:

```python
"web_03": {
    "id": "web_03",
    "category": "Web",
    "title": "SQL Injection Intro",
    "difficulty": "Medium",
    "points": 150,
    "description": "Try ' OR '1'='1 in the login form...",
    "hint": "Classic SQLi bypass",
    "flag": "iriiaCTF{sql_1nj3ct10n_1s_0ld_but_g0ld}",
    "url": None,
    "challenge_html": "web_sqli.html",   # optional interactive page
},
```

## 🔒 Production Security Notes

- Change `app.secret_key` to a long random string
- Use environment variables for secrets:
  ```python
  import os
  app.secret_key = os.environ.get("SECRET_KEY", "fallback")
  ```
- Add rate limiting on `/submit/<cid>` to prevent brute force
- For multi-user competitions, replace `session` with a database (SQLite/PostgreSQL)
