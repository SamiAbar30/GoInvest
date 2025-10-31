from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.secret_key = "SECRET_KEY_CHANGE_ME"

engine = create_engine("sqlite:///database.db")
Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    role = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    date = Column(String)
    like_number = Column(Integer, default=0)
    comments_number = Column(Integer, default=0)
    contact_number = Column(Integer, default=0)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", backref="posts")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    content = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

    post_id = Column(Integer, ForeignKey("posts.id"))
    post = relationship("Post", backref="comments")

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")


def time_ago(date):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    diff = datetime.utcnow() - date
    days = diff.days
    if days == 0:
        return "Today"
    elif days == 1:
        return "1 day ago"
    return f"{days} days ago"

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.query(User).get(int(user_id))


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    posts = db.query(Post).all()
    

    for p in posts:
        p.time_ago = time_ago(p.date)

    return render_template("home.html", user=current_user, posts=posts, pages="home")


@app.route("/post/<int:post_id>")
@login_required
def view_post(post_id):
    post = db.query(Post).filter_by(id=post_id).first()
    comments = db.query(Comment).filter_by(post_id=post_id).order_by(Comment.date.desc()).all()
    if not post:
        return redirect(url_for("dashboard"))
    
    post.comments = comments
    for c in post.comments:
        c.time_ago = time_ago(c.date)

    return render_template("view-post.html", user=current_user, post=post, pages="home")

@app.route("/post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        p = Post(
            title=title,
            description=description,
            date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            like_number=0,
            comments_number=0,
            contact_number=0,
            author_id=current_user.id
        )

        db.add(p)
        db.commit()
        return redirect(url_for("dashboard"))

    return render_template("create-post.html", user=current_user, pages="add_post")


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        return redirect(url_for("dashboard"))

    content = request.form["content"]
    if content.strip() == "":
        return redirect(url_for("view_post", post_id=post_id))

    comment = Comment(
        content=content,
        post_id=post.id,
        user_id=current_user.id
    )
    db.add(comment)
    post.comments_number += 1
    db.commit()
    return redirect(url_for("view_post", post_id=post_id))


@app.route("/post/<int:post_id>/like")
@login_required
def like_post(post_id):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        return redirect(url_for("dashboard"))

    post.like_number += 1
    db.commit()
    return redirect(url_for("view_post", post_id=post_id))


@app.route("/my_posts")
@login_required
def my_posts():
    posts = db.query(Post).filter_by(author_id=current_user.id).all()

    for p in posts:
        p.time_ago = time_ago(p.date)

    return render_template("home.html", posts=posts, user=current_user, pages="my_post")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        role = request.form["role"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if db.query(User).filter_by(email=email).first():
            flash("Email already used")
            return redirect(url_for("register"))

        user = User(name=name, surname=surname, role=role, email=email, password=password)
        db.add(user)
        db.commit()
        flash("Account created successfully")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.query(User).filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Incorrect credentials")
            return redirect(url_for("login"))
        
        login_user(user)
        return redirect(url_for("dashboard"))
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)