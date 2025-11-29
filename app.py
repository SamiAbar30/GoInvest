from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
import re

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
    tags = relationship("PostTag", back_populates="post")
    views = Column(Integer, default=0)


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    content = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

    post_id = Column(Integer, ForeignKey("posts.id"))
    post = relationship("Post", backref="comments")

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

    category_id = Column(Integer, ForeignKey("tag_categories.id"))
    category = relationship("TagCategory", back_populates="tags")

    posts = relationship("PostTag", back_populates="tag")


class PostTag(Base):
    __tablename__ = "post_tags"
    id = Column(Integer, primary_key=True)
    
    post_id = Column(Integer, ForeignKey("posts.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))

    post = relationship("Post", back_populates="tags")
    tag = relationship("Tag", back_populates="posts")

class TagCategory(Base):
    __tablename__ = "tag_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    tags = relationship("Tag", back_populates="category")

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

def truncate_text(text, max_length=100):
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."

def add_line_break_every_2_sentences(text):
    if not text:
        return ""

    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    grouped = []
    for i in range(0, len(sentences), 2):
        group = " ".join(sentences[i:i+2])
        grouped.append(group)
    
    return '<span class="br"></span>'.join(grouped)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Fill the tags db
default_categories = {
  "Business": [
    {
      "name": "B2B",
      "description": "Business-to-Business; products or services intended for companies rather than individuals."
    },
    {
      "name": "B2C",
      "description": "Business-to-Consumer; products or services designed for direct end-users or customers."
    },
    {
      "name": "Startup",
      "description": "A newly created business focused on innovation, scalability, and rapid growth."
    },
    {
      "name": "Subscription",
      "description": "A recurring revenue model where customers pay periodically for continuous access to a product or service."
    }
  ],
  
  "Education": [
    {
      "name": "EdTech",
      "description": "Educational technology solutions designed to enhance learning experiences through digital tools."
    },
    {
      "name": "KidsEducation",
      "description": "Learning programs, tools, or platforms created specifically for children’s education."
    },
    {
      "name": "LearningApp",
      "description": "A mobile or web application designed to support learning through interactive or structured content."
    },
    {
      "name": "DigitalLearning",
      "description": "Education delivered through digital platforms, enabling remote or flexible learning experiences."
    }
  ],

  "Health": [
    {
      "name": "HealthTech",
      "description": "Innovative technology solutions aimed at improving healthcare services, diagnostics, or patient experience."
    },
    {
      "name": "Wellness",
      "description": "Products or services focused on promoting well-being, balance, and healthy lifestyle habits."
    },
    {
      "name": "Nutrition",
      "description": "Solutions or information related to healthy eating, dietary optimization, or personalized meal plans."
    },
    {
      "name": "MentalHealth",
      "description": "Tools or services supporting mental well-being, mindfulness, stress management, and emotional health."
    }
  ],

  "Sustainability": [
    {
      "name": "EcoFriendly",
      "description": "Products or services designed to minimize environmental impact through sustainable practices."
    },
    {
      "name": "ZeroWaste",
      "description": "A lifestyle or approach aiming to eliminate waste by reusing, recycling, and reducing consumption."
    },
    {
      "name": "UrbanFarming",
      "description": "Growing food in cities using innovative or small-scale agricultural methods."
    }
  ],

  "Tech": [
    {
      "name": "AI",
      "description": "Artificial Intelligence technologies used to automate tasks, provide insights, or enhance user experiences."
    },
    {
      "name": "Gamification",
      "description": "The use of game mechanics to increase engagement, motivation, or learning."
    },
    {
      "name": "SmartHome",
      "description": "Connected devices and systems designed to automate and improve home living."
    }
  ]
}

for category_name, tag_list in default_categories.items():
    cat = db.query(TagCategory).filter_by(name=category_name).first()
    if not cat:
        cat = TagCategory(name=category_name)
        db.add(cat)
        db.commit()

    for tag_obj in tag_list:
        tag = db.query(Tag).filter_by(name=tag_obj["name"]).first()
        if not tag:
            tag = Tag(name=tag_obj["name"], description=tag_obj["description"], category_id=cat.id)
            db.add(tag)

db.commit()

@login_manager.user_loader
def load_user(user_id):
    return db.query(User).get(int(user_id))


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    posts = db.query(Post).order_by(Post.views.desc()).all()
    

    for p in posts:
        p.time_ago = time_ago(p.date)
        p.short_description = truncate_text(p.description, max_length=150)

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

    post_tags = (
    db.query(PostTag)
    .filter_by(post_id=post_id)
    .join(Tag, PostTag.tag_id == Tag.id)
    .all()
    )
    post.tags_list = [pt.tag.name for pt in post_tags]

    post.description_with_breaks = add_line_break_every_2_sentences(post.description)

    post.views = (post.views or 0) + 1
    db.commit()

    return render_template("view-post.html", user=current_user, post=post, pages="home")

@app.route("/post", methods=["GET", "POST"])
@login_required
def create_post():
    tags = db.query(Tag).all()
    categories = db.query(TagCategory).all()
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

        selected_tags = request.form.getlist("tags")

        for tag_id in selected_tags:
            db.add(PostTag(post_id=p.id, tag_id=int(tag_id)))

        db.commit()

        return redirect(url_for("dashboard"))

    return render_template("create-post.html", user=current_user, tags=tags, categories=categories, pages="add_post")


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

@app.route("/inbox")
@login_required
def inbox():

    return render_template("inbox.html", user=current_user, pages="inbox")

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


@app.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("qs", "").strip()

    if not query:
        return render_template("search.html", user=current_user, posts=[], q=query)

    posts_title_desc = db.query(Post).filter(
        (Post.title.ilike(f"%{query}%")) |
        (Post.description.ilike(f"%{query}%"))
    ).all()

    posts_author = (
        db.query(Post)
        .join(User, Post.author_id == User.id)
        .filter(
            (User.name.ilike(f"%{query}%")) |
            (User.surname.ilike(f"%{query}%"))
        )
        .all()
    )

    posts_tags = (
        db.query(Post)
        .join(PostTag, Post.id == PostTag.post_id)
        .join(Tag, Tag.id == PostTag.tag_id)
        .filter(Tag.name.ilike(f"%{query}%"))
        .all()
    )

    results = list({post.id: post for post in posts_title_desc + posts_author + posts_tags}.values())

    for p in results:
        p.time_ago = time_ago(p.date)
        p.short_description = truncate_text(p.description, 150)

        post_tags = (
            db.query(PostTag)
            .filter_by(post_id=p.id)
            .join(Tag, PostTag.tag_id == Tag.id)
            .all()
        )
        p.tags_list = [t.tag.name for t in post_tags]

    return render_template("home.html", user=current_user, posts=results, qs=query)

if __name__ == "__main__":
    app.run(debug=True)