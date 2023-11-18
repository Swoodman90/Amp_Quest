from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, BooleanField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


app = Flask(__name__) 
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['LOGIN_DISABLED'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Must be logged in to view this page!'
login_manager.init_app(app)

#@login_manager.unauthorized_handler
#def unauthorized():
    #return "You must be logged in to view this page."


class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    joined_at_date = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, index=True, unique=False)
    #comment_date = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

with app.app_context():
    db.create_all()


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Re-Enter Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField('Log In')


class CommentForm(FlaskForm):
    comment = TextAreaField('Leave A Comment:', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password!')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome {user.username}!')
        return redirect(url_for('audio'))
    return render_template("login.html", template_form=form)


@app.route('/audio', methods=['GET', 'POST'])
@login_required
def audio():
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(text=form.comment.data)
        with app.app_context():
            db.session.add(comment)
            try:
                db.session.commit()
            except:
                db.session.rollback()
            flash('Comment posted!')
    return render_template('audio.html', comments=Comment.query.all(), template_form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        with app.app_context():
            db.session.add(user)
            try:
                db.session.commit()
            except:
                db.session.rollback()
            flash('Account registered!')
        #return redirect(url_for('index'))
    return render_template('register.html', template_form=form)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Log Out Successful!')
    return redirect(url_for('index'))


@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('audio'))



