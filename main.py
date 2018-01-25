from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:happytree@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'preciousshoes'

class Blog(db.Model):    
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(100))
    body = db.Column(db.String(2500))    
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):    
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True)
    pw_hash = db.Column(db.String(120), nullable=False)
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():    
    allowed_routes = ['login', 'index', 'signup', 'static', 'logout'] 
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/signup', methods=["POST", "GET"])
def signup():    
    if request.method == "GET":
        return render_template('signup.html', page_title="signup")
    
    username = request.form["username"]
    password = request.form["password"]
    verify = request.form["verify"]
    user = User.query.filter_by(username=username).first()
    
    if username == "":
        username_error = "Introduce yourself!"
    elif len(username) < 3:
        username_error = "Sorry 2 nitpick, but your username needs to be 3 characters or more ;)"
    elif user: 
        username_error = "Aw ... that name is taken. You do you."
    else:
        username_error = ""    
    if password == "" and not user: 
        password_error = "Security is everything. Add a password!"
    elif len(password) < 3 and not user: 
        password_error = "Aim for at least 3 characters, k?"
    else:
        password_error = ""    
    if verify == "" and not user: 
        verify_error = "Do us a solid and just double-check for accuracy!"
    elif verify != password and not user: 
        verify_error = "Try that again please!"
    else:
        verify_error = ""    
    if not username_error and not password_error and not verify_error:
        if request.method == "POST":
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
    else:        
        return render_template('signup.html', page_title = "signup", username = username, username_error = username_error, 
            password_error = password_error, verify_error = verify_error)    

@app.route('/login', methods=["POST", "GET"])
def login():    
    if request.method == "GET":
        return render_template('login.html', page_title="login")
    
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    
    if username == "":
        username_error = "Announce yourself!"
    elif not user: 
        username_error = "Sorry! We don't know you yet!"
    else:        
        username_error = ""    
    if password == "" and user: 
        password_error = "What's the password?" 
    elif user: 
        if not check_pw_hash(password, user.pw_hash):
            password_error = "Tsk! Tsk!"
        else:
            password_error = ""
    elif not user: 
        password_error = ""    
    if username_error == "" and  password_error == "":
        if request.method == 'POST':
            if user and check_pw_hash(password, user.pw_hash):
                session['username'] = username
                flash("logged in")
                return redirect('/newpost')    
    else:
        return render_template('login.html', page_title = "login", username = username, 
            username_error = username_error, password_error = password_error)

@app.route('/', methods=["POST", "GET"])
def index():    
    users = User.query.all()
    return render_template('index.html', page_title = "storytellerz", users = users)
    
@app.route('/logout')
def logout():    
    if session:
        del session['username']
        flash("logged out")
    return redirect('/blog')

@app.route('/blog', methods=["POST", "GET"])
def list_blogs():    
    entries = Blog.query.all()    
    
    if "id" in request.args:
        id = request.args.get('id')
        entry = Blog.query.get(id)
        
        return render_template('entries.html', page_title="Storytime", title = entry.title, body = entry.body, owner = entry.owner)
    
    if "user" in request.args:
        owner_id = request.args.get('user')
        userEntries = Blog.query.filter_by(owner_id=owner_id)
        username = User.query.get(owner_id)

        return render_template('singleUser.html', page_title = "Storyz", userEntries = userEntries, user = username)    
    return render_template('posts.html', page_title="Blog", entries = entries)

@app.route('/newpost', methods=["POST", "GET"])
def add_entry():    
    
    if request.method == "GET":
        return render_template('newpost.html', page_title="blog")
    
    title = request.form["title"]
    body = request.form["body"]
    
    if title == "":        
        title_error = "Every good story needz a name!"
    else:        
        title_error = ""    
    if body == "":
        body_error = "Surely you meant to write something!"
    elif len(body) > 2500:
        body_error = "Wrap it up! Storyz cannot contain more than 2500 characterz!"
    else:
        body_error = ""    
    
    if not title_error and not body_error:
        if request.method == "POST":
            owner = User.query.filter_by(username=session['username']).first()
            new_entry = Blog(title, body, owner) 
            db.session.add(new_entry)
            db.session.commit()
        
        return render_template('entries.html', page_title = "Success!", title = title, body = body, owner = owner)
    else:        
        return render_template('newpost.html', page_title = "Story", title = title, 
            title_error = title_error, body = body, body_error = body_error)

if __name__ == '__main__':
    app.run()