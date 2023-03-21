from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from threading import Thread

from flask import Flask, flash, Markup, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_mail import Mail, Message
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from randimage import get_random_image
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.urls import url_parse
from wtforms import BooleanField, EmailField, FieldList, FormField, IntegerRangeField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp, ValidationError


class Config(object):
    DB_USER = os.environ.get('PG_USER')
    DB_PASSWD = os.environ.get('PG_PASSWD')
    DB_URL = f'postgresql://{DB_USER}:{DB_PASSWD}@localhost:5432/ml'
    SQLALCHEMY_DATABASE_URI = DB_URL
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [os.environ.get('ADMIN_EMAIL')]
    LEAGUES_PER_PAGE = 9
    SONGS_PER_PAGE = 10
    USERS_PER_PAGE = 20

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    passwd = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class SignUpForm(FlaskForm):
    username_max_length = 20
    username_min_length = 4
    passwd_min_length = 7
    name_max_length = 65
    user_regex_msg = 'Usernames can only be alphanumeric'
    user_max_length_msg = f'Usernames must be {username_min_length} to {username_max_length} characters long'
    name_max_length_msg = f'Names cannot be longer than {name_max_length} characters'
    passwd_length_msg = f'Passwords must be at least {passwd_min_length} characters long'
    username = StringField('Username', validators=[DataRequired(), Regexp('\w', message=user_regex_msg), Length(max=username_max_length, min=username_min_length, message=user_max_length_msg)])
    passwd = PasswordField('Password', validators=[DataRequired(), Length(min=passwd_min_length, message=passwd_length_msg)])
    passwd2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('passwd')])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired(), Length(max=name_max_length, message=name_max_length_msg)])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already registered')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email address is already associated with a user')

class CreateLeagueForm(FlaskForm):
    name_max_length = 48
    descr_max_length = 128
    name_max_length_msg = f'League names cannot be longer than {name_max_length} characters long'
    descr_max_length_msg = f'League descriptions cannot be longer than {descr_max_length} characters long'
    name = StringField('League Name', validators=[DataRequired(), Length(max=name_max_length, message=name_max_length_msg)])
    submit_days = IntegerRangeField('Days to Submit', default=2, validators=[DataRequired(), NumberRange(min=1, max=30)])
    vote_days = IntegerRangeField('Days to Vote', default=5, validators=[DataRequired(), NumberRange(min=1, max=30)])
    descr = TextAreaField('League Description', render_kw={"rows": 30, "cols": 50}, validators=[Optional(), Length(max=descr_max_length, message=descr_max_length_msg)])
    upvotes = IntegerRangeField('Total Upvotes Per Voter', default=10, validators=[DataRequired(), NumberRange(min=0, max=50)])
    downvotes = IntegerRangeField('Total Downvotes Per Voter', default=1, validators=[DataRequired(), NumberRange(min=0, max=50)])
    round_count = IntegerRangeField('Total Number of Rounds', default=5, validators=[DataRequired(), NumberRange(min=1, max=20)])
    submit = SubmitField('Create League')

class RoundsForm(FlaskForm):
    name_max_length = 48
    descr_max_length = 128
    name_max_length_msg = f'Round names cannot be longer than {name_max_length} characters long'
    descr_max_length_msg = f'Round descriptions cannot be longer than {descr_max_length} characters long'
    name = StringField('Round Name', validators=[DataRequired(), Length(max=name_max_length, message=name_max_length_msg)])
    descr = StringField('Description', validators=[DataRequired(), Length(max=descr_max_length, message=descr_max_length_msg)])

class AddRoundsForm(FlaskForm):
    rounds = FieldList(FormField(RoundsForm), min_entries=1, max_entries=20)
    submit = SubmitField('Create Rounds')


app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY')
app.config.from_object(Config)
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_mgr = LoginManager(app)
login_mgr.login_view = 'login'
mail = Mail(app)
moment = Moment(app)


# setup mail handler for errors and log locally too
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Music League failure !',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ml.log', maxBytes=100240, backupCount=4)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Music League startup')


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, unique=True)
    email = db.Column(db.String(64), unique=True)
    passwd = db.Column(db.String(128))
    name = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=True)
    icon_id = db.Column(db.Integer, db.ForeignKey('icons.id'), nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, passwd):
        self.passwd = generate_password_hash(passwd)

    def check_password(self, passwd):
        return check_password_hash(self.passwd, passwd)

class Icons(UserMixin, db.Model):
    __tablename__ = 'icons'
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.LargeBinary)


class Leagues(UserMixin, db.Model):
    __tablename__ = 'leagues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    submit_days = db.Column(db.Integer)
    vote_days = db.Column(db.Integer)
    descr = db.Column(db.String(256), nullable=True)
    end_date = db.Column(db.DateTime)
    upvotes = db.Column(db.Integer, default=10)
    downvotes = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    round_count = db.Column(db.Integer, db.CheckConstraint('round_count > 0', name='positive_round_cnt'), default=1)

    def __repr__(self):
        return f'<Name {self.name}>'

    def set_end_date(self, submit_days, vote_days):
        now = datetime.utcnow()
        total_days = (submit_days + vote_days) * round_count
        end_date = now + timedelta(days=total_days)
        self.end_date = end_date

class LeagueMembers(UserMixin, db.Model):
    __tablename__ = 'league_members'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<League Id {self.league_id}\tUser Id {self.user_id}>'

class Rounds(UserMixin, db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    name = db.Column(db.String(92))
    descr = db.Column(db.String(128))

    def __repr__(self):
        return f'<Name {self.name}>'

class Songs(UserMixin, db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    song_url = db.Column(db.String(512))
    descr = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return f'<Id {self.id}\tURL {self.song_url}>'

class Votes(UserMixin, db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    votes = db.Column(db.Integer, default=0)
    comment = db.Column(db.String(256), nullable=True)
    vote_date = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f'<Song Id {self.song_id}\tVotes {self.votes}>'

@app.route('/')
@app.route('/index')
def default():
    content = 'ML Content!'
    return render_template('index.html', title="CPU Music League", content=content)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('default'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.passwd.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('default')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/leagues', methods=['GET', 'POST'])
def leagues():
    """View/Create a new league."""
    page = request.args.get('page', 1, type=int)
    leagues = Leagues.query.order_by(Leagues.end_date.desc()).paginate(page=page, per_page=app.config['LEAGUES_PER_PAGE'], error_out=False)
    next_url = url_for('leagues', page=leagues.next_num) if leagues.has_next else None
    prev_url = url_for('leagues', page=leagues.prev_num) if leagues.has_prev else None
    return render_template('leagues.html', title='View / Create Music Leagues', leagues=leagues.items, next_url=next_url, prev_url=prev_url)


@app.route('/league', methods=['GET', 'POST'])
def league():
    """View/Join a league."""
    league_id = request.args.get('id', 0, type=int)
    if league_id == 0:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    league = Leagues.query.get(league_id)
    if not league:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    return render_template('league.html', title='View / Join this Music League', league=league)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new league."""
    form = CreateLeagueForm()
    if form.validate_on_submit():
        user_id = current_user.get_id()
        total_days = int(form.submit_days.data) + int(form.vote_days.data)
        league = Leagues(name=form.name.data, submit_days=form.submit_days.data, vote_days=form.vote_days.data, descr=form.descr.data, upvotes=form.upvotes.data, downvotes=form.downvotes.data, round_count=form.round_count.data, owner_id=user_id)
        league.set_end_date(form.submit_days.data, form.vote_days.data)
        db.session.add(league)
        db.session.commit()
        flash_msg = Markup(f'Congratulations {current_user.name}! <br>You have created a new league called <b>{form.name.data}</b> which will close in {total_days} days')
        flash(flash_msg)
        add_rounds = url_for('add_rounds', league_id=league.id, round_count=form.round_count.data)
        return redirect(add_rounds)
    return render_template('create.html', title='Create a new Music League', form=form)


@app.route('/add_rounds', methods=['GET', 'POST'])
@login_required
def add_rounds():
    """Add rounds to the new league."""
    league_id = request.args.get('league_id', 0, type=int)
    round_count = request.args.get('round_count', 0, type=int)
    if league_id == 0 or round_count == 0:
        flash('Invalid league specified', 'error')
        return redirect(url_for('leagues'))
    form = AddRoundsForm()
    if form.validate_on_submit():
        for round_data in form.data['rounds']:
            round_record = Rounds(league_id=league_id, name=round_data['name'], descr=round_data['descr'])
            db.session.add(round_record)
        db.session.commit()
        flash_msg = Markup(f'{round_count} rounds added to your league')
        flash(flash_msg)
        return redirect(url_for('league', id=league_id))
    return render_template('create_rounds.html', title='Add rounds to this league', form=form, id=league_id, count=round_count)


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    """List registered members/users."""
    page = request.args.get('page', 1, type=int)
    users = Users.query.order_by(Users.username).paginate(page=page, per_page=app.config['USERS_PER_PAGE'], error_out=False)
    next_url = url_for('users', page=users.next_num) if users.has_next else None
    prev_url = url_for('users', page=users.prev_num) if users.has_prev else None
    return render_template('members.html', title='Music League Members', users=users.items, next_url=next_url, prev_url=prev_url)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('default'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('default'))
    form = SignUpForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, email=form.email.data, name=form.name.data)
        user.set_password(form.passwd.data)
        db.session.add(user)
        db.session.commit()
        flash(f'{form.name.data} thanks for registering as {form.username.data} ({form.email.data})')
        return redirect(url_for('login'))
    return render_template('signup.html', title="CPU Music League Sign Up", form=form)


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """Send email."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


# used by 'flask shell' to setup query context
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Icons': Icons, 'Leagues': Leagues, 'Rounds': Rounds, 'Songs': Songs, 'Votes': Votes}


@login_mgr.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()