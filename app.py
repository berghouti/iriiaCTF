from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, flash, abort, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "iriiaCTF_dev_secret_change_in_prod")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ctf.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folders
CHALLENGES_TEMPLATE_DIR = os.path.join(app.root_path, "templates", "challenges")
UPLOAD_DIR               = os.path.join(app.root_path, "static", "uploads")
os.makedirs(CHALLENGES_TEMPLATE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ctf.db"
UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads")
# Categories that use an interactive HTML page (iframe)
HTML_CATEGORIES = {"Web"}
# Categories that use a downloadable file attachment
FILE_CATEGORIES = {"Forensics", "OSINT", "Misc", "Reverse", "Pwn", "Crypto", "Linux"}

db = SQLAlchemy(app)

# ═══════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created  = db.Column(db.DateTime, default=datetime.utcnow)
    solves   = db.relationship("Solve", backref="user", lazy=True)

    @property
    def score(self):
        return sum(s.challenge.points for s in self.solves if s.challenge)

    @property
    def solve_count(self):
        return len(self.solves)

    @property
    def last_solve_time(self):
        if not self.solves:
            return ""
        return max(s.solved_at for s in self.solves).isoformat()


class Challenge(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    slug           = db.Column(db.String(64), unique=True, nullable=False)
    title          = db.Column(db.String(128), nullable=False)
    category       = db.Column(db.String(32), nullable=False)
    difficulty     = db.Column(db.String(16), nullable=False)
    points         = db.Column(db.Integer, nullable=False)
    description    = db.Column(db.Text, nullable=False)
    hint           = db.Column(db.Text, default="")
    flag           = db.Column(db.String(256), nullable=False)
    challenge_html = db.Column(db.String(128), default="")   # for HTML_CATEGORIES
    download_file  = db.Column(db.String(256), default="")   # for FILE_CATEGORIES
    external_url   = db.Column(db.String(512), default="")
    visible        = db.Column(db.Boolean, default=True)
    created        = db.Column(db.DateTime, default=datetime.utcnow)
    solves         = db.relationship("Solve", backref="challenge", lazy=True)

    @property
    def solve_count(self):
        return len(self.solves)


class Solve(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=False)
    solved_at    = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "challenge_id"),)


# ═══════════════════════════════════════════════════════════════
#  SEED DATA
# ═══════════════════════════════════════════════════════════════

SEED_CHALLENGES = [
    dict(slug="web_01", title="Inspector Gadget", category="Web", difficulty="Easy", points=50,
         description="Every browser has a secret weapon — the developer tools. "
                     "Open this page's source and find the hidden flag lurking in an HTML comment.",
         hint="Right-click → View Page Source, or press F12 → Elements tab.",
         flag="iriiaCTF{h1dd3n_1n_pl41n_s1ght}", challenge_html="web_inspector.html"),

    dict(slug="web_02", title="Cookie Monster", category="Web", difficulty="Medium", points=100,
         description="The login panel sets a cookie that controls your access level. "
                     "Inspect and modify it to become an admin and reveal the flag.",
         hint="DevTools → Application → Cookies. Change <b>role</b> to <b>admin</b>.",
         flag="iriiaCTF{c00k13s_4r3_t4sty_but_d4ng3r0us}", challenge_html="web_cookie.html"),

    dict(slug="crypto_01", title="Caesar's Secret", category="Crypto", difficulty="Easy", points=50,
         description="Julius Caesar used a simple shift cipher. "
                     "Decode: <code>luullNFWC{fkliwhu_flskhu_lv_ixq}</code>",
         hint="Shift each letter back by 3. Symbols like { } _ stay unchanged.",
         flag="iriiaCTF{cipher_cipher_is_fun}", challenge_html="crypto_caesar.html"),

    dict(slug="crypto_02", title="Base Basics", category="Crypto", difficulty="Easy", points=75,
         description="Decode this Base64 string:<br>"
                     "<code>aXJpaWFDVEZ7YjRzM182NF9pczNfbjB0X2VuY3J5cHQxMG59</code>",
         hint="Use CyberChef or Python: import base64; base64.b64decode('...')",
         flag="iriiaCTF{b4s3_64_is3_n0t_encryt10n}", challenge_html="crypto_base64.html"),

    dict(slug="crypto_03", title="XOR Files", category="Crypto", difficulty="Medium", points=125,
         description="A flag was XOR-encrypted with key <b>0x42</b>. Hex ciphertext:<br>"
                     "<code>2b303a3a3b4354467b78306f725f31735f6631756e7d</code>",
         hint="Python: data=bytes.fromhex('...'); print(bytes([b^0x42 for b in data]))",
         flag="iriiaCTF{x0r_1s_f1un}", challenge_html="crypto_xor.html"),

    dict(slug="forensics_01", title="Metadata Matters", category="Forensics", difficulty="Easy", points=50,
         description="Images carry hidden EXIF metadata. "
                     "Download the image and read its metadata to find the flag.",
         hint="Look through every EXIF field for the iriiaCTF{...} pattern.",
         flag="iriiaCTF{m3t4d4t4_t3lls_4ll}"),

    dict(slug="forensics_02", title="Strings Attached", category="Forensics", difficulty="Medium", points=100,
         description="Binary files hide readable text. Run <code>strings</code> on the downloaded binary.",
         hint="strings mystery_binary | grep iriiaCTF",
         flag="iriiaCTF{str1ngs_r3v34l_s3cr3ts}"),

    dict(slug="linux_01", title="Find the Flag", category="Linux", difficulty="Easy", points=50,
         description="Use the interactive terminal below to explore a filesystem. "
                     "A file named <code>flag.txt</code> is hidden somewhere. Find it and read it.",
         hint="find / -name flag.txt 2>/dev/null  — then  cat /path/to/flag.txt",
         flag="iriiaCTF{f1nd_c0mm4nd_1s_p0w3rful}", challenge_html="linux_find.html"),

    dict(slug="linux_02", title="Permission Denied?", category="Linux", difficulty="Easy", points=75,
         description="A script <code>reveal.sh</code> exists in the terminal below but it won't execute. "
                     "Fix its permissions and run it.",
         hint="chmod +x reveal.sh   then   ./reveal.sh",
         flag="iriiaCTF{chm0d_unl0cks_th3_w0rld}", challenge_html="linux_chmod.html"),

    dict(slug="linux_03", title="Grep Master", category="Linux", difficulty="Medium", points=100,
         description="A 200-line log file hides one flag. Use <code>grep</code> to find it in seconds.",
         hint="grep 'iriiaCTF' logfile.txt",
         flag="iriiaCTF{gr3p_s4v3s_t1m3_3v3ry_t1m3}", challenge_html="linux_grep.html"),

    dict(slug="linux_04", title="Pipe Dream", category="Linux", difficulty="Medium", points=125,
         description="Chain commands with pipes. Run:<br>"
                     "<code>echo 'fdn1M1RBQ2FpaXJp' | base64 -d | rev</code>",
         hint="Pipes pass output of one command as input to the next.",
         flag="iriiaCTF{p1p3s_4r3_m4g1c}", challenge_html="linux_pipes.html"),
]


def seed_db():
    if Challenge.query.count() == 0:
        for c in SEED_CHALLENGES:
            db.session.add(Challenge(**c))
        db.session.commit()
    if not User.query.filter_by(is_admin=True).first():
        db.session.add(User(
            username="admin",
            password=generate_password_hash("admin123"),
            is_admin=True
        ))
        db.session.commit()


# ═══════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        u = User.query.get(session["user_id"])
        if not u or not u.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None

@app.context_processor
def inject_globals():
    return dict(
        current_user=current_user(),
        HTML_CATEGORIES=HTML_CATEGORIES,
        FILE_CATEGORIES=FILE_CATEGORIES,
    )


# ═══════════════════════════════════════════════════════════════
#  FILE UPLOAD HELPERS
# ═══════════════════════════════════════════════════════════════

def save_challenge_html(file_obj, slug):
    """Save an uploaded HTML file into templates/challenges/ and return filename."""
    original = secure_filename(file_obj.filename)
    # Always name it after the slug to avoid collisions
    ext = os.path.splitext(original)[1].lower()
    if ext not in (".html", ".htm"):
        return None, "Challenge file must be an .html file."
    filename = f"{slug}{ext}"
    file_obj.save(os.path.join(CHALLENGES_TEMPLATE_DIR, filename))
    return filename, None

def save_download_file(file_obj, slug):
    """Save an uploaded attachment into static/uploads/ and return filename."""
    original = secure_filename(file_obj.filename)
    ext = os.path.splitext(original)[1].lower()
    # Prefix with slug so multiple challenges don't collide
    filename = f"{slug}_{original}"
    file_obj.save(os.path.join(UPLOAD_DIR, filename))
    return filename, None


# ═══════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    total_chals  = Challenge.query.filter_by(visible=True).count()
    total_points = db.session.query(db.func.sum(Challenge.points)).filter_by(visible=True).scalar() or 0
    total_users  = User.query.filter_by(is_admin=False).count()
    cats = [c[0] for c in
            db.session.query(Challenge.category).filter_by(visible=True).distinct().all()]
    return render_template("index.html",
                           total_chals=total_chals, total_points=total_points,
                           total_users=total_users, categories=cats)

@app.route("/learn")
def learn():
    return render_template("learn.html")

@app.route("/challenges")
@login_required
def challenges():
    user = current_user()
    cat  = request.args.get("cat", "All")
    cats = ["All"] + [c[0] for c in
            db.session.query(Challenge.category).filter_by(visible=True).distinct().all()]
    q = Challenge.query.filter_by(visible=True)
    if cat != "All":
        q = q.filter_by(category=cat)
    chals = q.order_by(Challenge.points).all()
    solved_ids  = {s.challenge_id for s in user.solves}
    total_chals = Challenge.query.filter_by(visible=True).count()
    return render_template("challenges.html",
                           challenges=chals, categories=cats, active_cat=cat,
                           solved_ids=solved_ids, user=user, total_chals=total_chals)

@app.route("/challenge/<slug>")
@login_required
def challenge_detail(slug):
    ch   = Challenge.query.filter_by(slug=slug, visible=True).first_or_404()
    user = current_user()
    solved_ids = {s.challenge_id for s in user.solves}
    return render_template("challenge_detail.html",
                           ch=ch, solved_ids=solved_ids, user=user)

@app.route("/submit/<slug>", methods=["POST"])
@login_required
def submit_flag(slug):
    ch   = Challenge.query.filter_by(slug=slug, visible=True).first_or_404()
    user = current_user()
    flag = (request.json or {}).get("flag", "").strip()
    if Solve.query.filter_by(user_id=user.id, challenge_id=ch.id).first():
        return jsonify({"ok": True, "msg": "Already solved! 🎉", "already": True})
    if flag == ch.flag:
        db.session.add(Solve(user_id=user.id, challenge_id=ch.id))
        db.session.commit()
        return jsonify({"ok": True, "msg": f"Correct! +{ch.points} points 🎉",
                        "points": ch.points})
    return jsonify({"ok": False, "msg": "Wrong flag. Keep trying! 💪"})

@app.route("/leaderboard")
def leaderboard():
    user  = current_user()
    users = User.query.filter_by(is_admin=False).all()
    board = sorted(users, key=lambda u: (-u.score, u.last_solve_time))
    total_chals = Challenge.query.filter_by(visible=True).count()
    solved_ids  = {s.challenge_id for s in user.solves} if user else set()
    return render_template("scoreboard.html",
                           board=board,
                           me=user,
                           solved_ids=solved_ids,
                           total_chals=total_chals)

@app.route("/api/leaderboard")
def api_leaderboard():
    users = User.query.filter_by(is_admin=False).all()
    board = sorted(
        [{"username": u.username, "score": u.score,
          "solves": u.solve_count, "last_solve": u.last_solve_time}
         for u in users],
        key=lambda x: (-x["score"], x["last_solve"])
    )
    return jsonify(board)

@app.route("/api/me/score")
def api_my_score():
    user = current_user()
    if not user:
        return jsonify({"score": 0, "solves": 0})
    return jsonify({"score": user.score, "solves": user.solve_count})

@app.route("/challenge-page/<slug>")
def challenge_page(slug):
    ch = Challenge.query.filter_by(slug=slug).first_or_404()
    if ch.challenge_html:
        return render_template(f"challenges/{ch.challenge_html}", ch=ch)
    return "No interactive page.", 404

@app.route("/download/<slug>")
@login_required
def download_challenge_file(slug):
    """Serve the downloadable file for a challenge (Forensics / OSINT / etc.)."""
    ch = Challenge.query.filter_by(slug=slug, visible=True).first_or_404()
    if not ch.download_file:
        abort(404)
    return send_from_directory(UPLOAD_DIR, ch.download_file, as_attachment=True)


# ═══════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/register", methods=["GET","POST"])
def register():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        if not username or not password:
            flash("All fields required.", "error")
        elif len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
        else:
            u = User(username=username, password=generate_password_hash(password))
            db.session.add(u)
            db.session.commit()
            session["user_id"] = u.id
            flash(f"Welcome, {username}! Start hacking! 🎉", "success")
            return redirect(url_for("challenges"))
    return render_template("auth/register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        u = User.query.filter_by(username=username).first()
        if u and check_password_hash(u.password, password):
            session["user_id"] = u.id
            flash(f"Welcome back, {u.username}!", "success")
            return redirect(request.args.get("next") or url_for("challenges"))
        flash("Invalid username or password.", "error")
    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ═══════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_index():
    challenges   = Challenge.query.order_by(Challenge.category, Challenge.points).all()
    users        = sorted(User.query.filter_by(is_admin=False).all(), key=lambda u: -u.score)
    total_solves = Solve.query.count()
    return render_template("admin/index.html",
                           challenges=challenges, users=users, total_solves=total_solves)


def _process_challenge_form(ch=None):
    """
    Shared logic for new/edit challenge form POST.
    Returns (ok: bool, error_msg: str | None, data: dict).
    """
    d    = request.form
    slug = ch.slug if ch else d.get("slug","").strip().replace(" ","_").lower()
    category = d.get("category", "Misc").strip()

    data = dict(
        title       = d.get("title","").strip(),
        category    = category,
        difficulty  = d.get("difficulty","Easy"),
        points      = max(1, int(d.get("points", 50) or 50)),
        description = d.get("description","").strip(),
        hint        = d.get("hint","").strip(),
        flag        = d.get("flag","").strip(),
        external_url= d.get("external_url","").strip(),
        visible     = "visible" in d,
        # Preserve existing values by default
        challenge_html = ch.challenge_html if ch else "",
        download_file  = ch.download_file  if ch else "",
    )

    # ── Handle HTML file upload (for HTML_CATEGORIES) ──────────────
    html_file = request.files.get("challenge_html_file")
    if html_file and html_file.filename:
        filename, err = save_challenge_html(html_file, slug)
        if err:
            return False, err, {}
        data["challenge_html"] = filename
    else:
        # Also allow plain text fallback (kept from old form)
        manual = d.get("challenge_html","").strip()
        if manual:
            data["challenge_html"] = manual

    # ── Handle downloadable file upload (for FILE_CATEGORIES) ──────
    dl_file = request.files.get("download_file")
    if dl_file and dl_file.filename:
        filename, err = save_download_file(dl_file, slug)
        if err:
            return False, err, {}
        data["download_file"] = filename

    return True, None, dict(slug=slug, **data)


@app.route("/admin/challenge/new", methods=["GET","POST"])
@admin_required
def admin_new_challenge():
    if request.method == "POST":
        ok, err, data = _process_challenge_form()
        slug = data.get("slug","")
        if not slug:
            flash("Slug is required.", "error")
        elif Challenge.query.filter_by(slug=slug).first():
            flash("Slug already exists — choose a different one.", "error")
        elif not ok:
            flash(err, "error")
        else:
            ch = Challenge(**data)
            db.session.add(ch)
            db.session.commit()
            flash(f"✅ Challenge '{ch.title}' created!", "success")
            return redirect(url_for("admin_index"))
    return render_template("admin/challenge_form.html", ch=None, action="new",
                           html_cats=HTML_CATEGORIES, file_cats=FILE_CATEGORIES)


@app.route("/admin/challenge/<int:cid>/edit", methods=["GET","POST"])
@admin_required
def admin_edit_challenge(cid):
    ch = Challenge.query.get_or_404(cid)
    if request.method == "POST":
        ok, err, data = _process_challenge_form(ch=ch)
        if not ok:
            flash(err, "error")
        else:
            for k, v in data.items():
                if k != "slug":          # slug is immutable
                    setattr(ch, k, v)
            db.session.commit()
            flash(f"✅ Challenge '{ch.title}' updated!", "success")
            return redirect(url_for("admin_index"))
    return render_template("admin/challenge_form.html", ch=ch, action="edit",
                           html_cats=HTML_CATEGORIES, file_cats=FILE_CATEGORIES)


@app.route("/admin/challenge/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_delete_challenge(cid):
    ch = Challenge.query.get_or_404(cid)
    title = ch.title
    Solve.query.filter_by(challenge_id=ch.id).delete()
    db.session.delete(ch)
    db.session.commit()
    flash(f"Challenge '{title}' deleted.", "info")
    return redirect(url_for("admin_index"))

@app.route("/admin/challenge/<int:cid>/toggle", methods=["POST"])
@admin_required
def admin_toggle_challenge(cid):
    ch = Challenge.query.get_or_404(cid)
    ch.visible = not ch.visible
    db.session.commit()
    return jsonify({"visible": ch.visible})

@app.route("/admin/user/<int:uid>/delete", methods=["POST"])
@admin_required
def admin_delete_user(uid):
    u = User.query.get_or_404(uid)
    username = u.username
    Solve.query.filter_by(user_id=u.id).delete()
    db.session.delete(u)
    db.session.commit()
    flash(f"User '{username}' deleted.", "info")
    return redirect(url_for("admin_index"))


# ═══════════════════════════════════════════════════════════════
#  BOOTSTRAP
# ═══════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    # ── Migrate existing DB: add download_file column if absent ──────
    with db.engine.connect() as conn:
        cols = [row[1] for row in conn.execute(
            db.text("PRAGMA table_info('challenge')")
        )]
        if "download_file" not in cols:
            conn.execute(db.text(
                "ALTER TABLE challenge ADD COLUMN download_file VARCHAR(256) DEFAULT ''"
            ))
            conn.commit()
    seed_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
