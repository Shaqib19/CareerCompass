from __future__ import annotations
from typing import Optional
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from models import db, User, Question, Attempt, seed_if_empty

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///careercompass.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return User.query.get(int(user_id))

@app.before_request
def ensure_db_seeded():
    db.create_all()
    seed_if_empty()

@app.route("/")
def index():
    return render_template("index.html", title="CareerCompass")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password required.")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("register"))
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully. Please login.")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("questions"))
        flash("Invalid credentials.")
        return redirect(url_for("login"))
    return render_template("login.html", title="Login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

def build_question_query():
    role = request.args.get("role", "")
    topic = request.args.get("topic", "")
    level = request.args.get("level", "")
    company = request.args.get("company", "")
    term = request.args.get("q", "")
    q = Question.query
    if role: q = q.filter_by(role=role)
    if topic: q = q.filter_by(topic=topic)
    if level: q = q.filter_by(level=level)
    if company: q = q.filter_by(company=company)
    if term:
        like = f"%{term}%"
        q = q.filter(or_(Question.title.ilike(like), Question.body.ilike(like)))
    return q

def distinct_filters():
    roles = [r[0] for r in db.session.query(Question.role).distinct().all()]
    topics = [t[0] for t in db.session.query(Question.topic).distinct().all()]
    companies = [c[0] for c in db.session.query(Question.company).distinct().all()]
    levels = ["Beginner", "Intermediate", "Expert"]
    return roles, topics, companies, levels

@app.route("/questions")
@login_required
def questions():
    page = request.args.get("page", 1, type=int)
    query = build_question_query()
    pagination = query.order_by(Question.id.desc()).paginate(page=page, per_page=8, error_out=False)

    roles, topics, companies, levels = distinct_filters()
    return render_template(
        "questions.html",
        items=pagination.items,
        pagination=pagination,
        role=request.args.get("role", ""),
        topic=request.args.get("topic", ""),
        level=request.args.get("level", ""),
        company=request.args.get("company", ""),
        term=request.args.get("q", ""),
        roles=roles, topics=topics, companies=companies, levels=levels,
        title="Questions"
    )

@app.route("/practice/level/<level>")
@login_required
def practice_level(level: str):
    page = request.args.get("page", 1, type=int)
    query = Question.query.filter_by(level=level)
    pagination = query.order_by(Question.id.desc()).paginate(page=page, per_page=8, error_out=False)
    roles, topics, companies, levels = distinct_filters()
    return render_template(
        "questions.html",
        items=pagination.items,
        pagination=pagination,
        role="", topic="", level=level, company="", term="",
        roles=roles, topics=topics, companies=companies, levels=levels,
        title=f"{level} Practice"
    )

@app.route("/question/<int:qid>", methods=["GET", "POST"])
@login_required
def question_detail(qid: int):
    q = Question.query.get_or_404(qid)
    explanation_shown = False
    correct = None
    submitted = None
    if request.method == "POST":
        submitted = request.form.get("answer", "").strip()
        if q.type == "mcq":
            correct = (submitted == q.correct_option)
        else:
            exact = submitted.lower() == (q.answer or "").lower()
            has_kw = bool(q.keyword) and q.keyword.lower() in submitted.lower()
            correct = exact or has_kw
        attempt = Attempt(user_id=current_user.id, question_id=q.id, is_correct=bool(correct), submitted=submitted)
        db.session.add(attempt)
        db.session.commit()
        explanation_shown = True
    return render_template("question_detail.html", q=q, submitted=submitted, correct=correct, explanation_shown=explanation_shown, title=q.title)

@app.route("/dashboard")
@login_required
def dashboard():
    total = Attempt.query.filter_by(user_id=current_user.id).count()
    correct = Attempt.query.filter_by(user_id=current_user.id, is_correct=True).count()
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    recent = Attempt.query.filter_by(user_id=current_user.id).order_by(Attempt.created_at.desc()).limit(10).all()
    return render_template("dashboard.html", total=total, correct=correct, accuracy=accuracy, recent=recent, title="Dashboard")

if __name__ == "__main__":
    app.run(debug=True)
