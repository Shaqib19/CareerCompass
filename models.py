from __future__ import annotations
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="mcq")       # "mcq" or "short"
    level = db.Column(db.String(32), default="Beginner")  # Beginner/Intermediate/Expert
    role = db.Column(db.String(64), default="SDE")        # SDE, Backend, Data Analyst, etc.
    topic = db.Column(db.String(64), default="Arrays")
    company = db.Column(db.String(64), default="General")

    # MCQ fields
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    correct_option = db.Column(db.String(1))

    # Short answer fields
    answer = db.Column(db.Text)
    keyword = db.Column(db.String(64))

    # Explanation
    explanation = db.Column(db.Text)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    submitted = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def seed_if_empty():
    if Question.query.first():
        return
    samples = [
        Question(
            title="Two Sum (Array)",
            body="Given an array and target, return indices of two numbers adding to target.",
            type="mcq", level="Beginner", role="SDE", topic="Arrays", company="General",
            option_a="Use two loops O(n^2)",
            option_b="Use hash map to store complements O(n)",
            option_c="Sort then two pointers O(n log n)",
            option_d="Binary search for each element O(n log n)",
            correct_option="B",
            explanation="Use a dict value->index. For each x, check target-x in dict; else store x. O(n).",
        ),
        Question(
            title="SQL: Top N per group",
            body="Select highest salary per department.",
            type="short", level="Intermediate", role="Data Analyst", topic="SQL", company="General",
            answer="window function", keyword="dense_rank",
            explanation="Use DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)=1.",
        ),
        Question(
            title="REST: Idempotent methods",
            body="Which HTTP methods are idempotent?",
            type="mcq", level="Beginner", role="Backend", topic="HTTP", company="General",
            option_a="GET, PUT, DELETE, HEAD, OPTIONS, TRACE",
            option_b="POST only",
            option_c="GET and POST",
            option_d="PUT only",
            correct_option="A",
            explanation="Idempotent: GET, PUT, DELETE, HEAD, OPTIONS, TRACE; POST is not.",
        ),
        Question(
            title="Two Pointers: Pair Sum Sorted",
            body="Given a sorted array and target, find any pair that sums to target.",
            type="mcq", level="Beginner", role="SDE", topic="Two Pointers", company="General",
            option_a="Nested loops O(n^2)", option_b="Hash set O(n)", option_c="Two pointers O(n)", option_d="Binary search O(n log n)",
            correct_option="C",
            explanation="For sorted arrays, left+right pointer technique runs in O(n) and O(1) space.",
        ),
        Question(
            title="SQL: COUNT vs COUNT(*)",
            body="Is COUNT(column) different from COUNT(*)? Explain.",
            type="short", level="Beginner", role="Data Analyst", topic="SQL", company="General",
            answer="count star", keyword="null",
            explanation="COUNT(*) counts rows; COUNT(col) skips NULL in that column.",
        ),
        Question(
            title="Backend: 201 for POST",
            body="What status code for a resource created via POST?",
            type="mcq", level="Beginner", role="Backend", topic="HTTP", company="General",
            option_a="200 OK", option_b="201 Created", option_c="204 No Content", option_d="409 Conflict",
            correct_option="B",
            explanation="201 Created indicates a new resource was created; include Location header when applicable.",
        ),
    ]
    db.session.bulk_save_objects(samples)
    db.session.commit()
