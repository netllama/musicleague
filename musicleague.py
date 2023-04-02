from dataclasses import dataclass
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
from urllib.parse import urlparse
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.urls import url_parse
from wtforms import BooleanField, EmailField, FieldList, FormField, HiddenField, IntegerField, IntegerRangeField, PasswordField, StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp, ValidationError
import youtube_api


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
    YT_API_KEY = os.environ.get('YT_API_KEY')

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

class SubmitSongForm(FlaskForm):
    descr_max_length = 128
    descr_max_length_msg = f'Song descriptions cannot be longer than {descr_max_length} characters long'
    user = HiddenField('user_id', validators=[DataRequired()])
    round = HiddenField('round_id', validators=[DataRequired()])
    league = HiddenField('league_id', validators=[DataRequired()])
    song_url = URLField('Youtube song link', validators=[DataRequired()])
    descr = TextAreaField('Song description', render_kw={"rows": 30, "cols": 50}, validators=[Optional(), Length(max=descr_max_length, message=descr_max_length_msg)])
    submit = SubmitField('Submit Song')

class VoteForm(FlaskForm):
    comment_max_length = 128
    comment_max_length_msg = f'Song comment cannot be longer than {comment_max_length} characters long'
    round = HiddenField('round_id', validators=[DataRequired()])
    league = HiddenField('league_id', validators=[DataRequired()])
    song = HiddenField('song_id', validators=[DataRequired()])
    vote = IntegerField('vote', default=0, validators=[DataRequired()])
    comment = TextAreaField('Song comment', render_kw={"rows": 30, "cols": 50}, validators=[Optional(), Length(max=comment_max_length, message=comment_max_length_msg)])
    submit = SubmitField('Submit Votes')


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
    icons = db.relationship('Icons', back_populates='user')
    leagues = db.relationship('Leagues', back_populates='user')
    members = db.relationship('LeagueMembers', back_populates='user')
    songs = db.relationship('Songs', back_populates='user')
    votes = db.relationship('Votes', back_populates='user')

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
    user = db.relationship('Users', back_populates ='icons')

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
    user = db.relationship('Users', back_populates='leagues')
    members = db.relationship('LeagueMembers', back_populates='leagues')
    rounds = db.relationship('Rounds', back_populates='leagues')
    songs = db.relationship('Songs', back_populates='leagues')
    votes = db.relationship('Votes', back_populates='leagues')

    def __repr__(self):
        return f'<Name {self.name}>'

    def set_end_date(self, submit_days, vote_days, round_count):
        now = datetime.utcnow()
        total_days = (submit_days + vote_days) * round_count
        end_date = now + timedelta(days=total_days)
        app.logger.debug(f'now = {now}\tsubmit_days = {submit_days}\tround_count = {round_count}\tvote_days = {vote_days}\tend_date = {end_date}')
        self.end_date = end_date

class LeagueMembers(UserMixin, db.Model):
    __tablename__ = 'league_members'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users', back_populates='members')
    leagues = db.relationship('Leagues', back_populates='members')

    def __repr__(self):
        return f'<League Id {self.league_id}\tUser Id {self.user_id}>'

class Rounds(UserMixin, db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    name = db.Column(db.String(92))
    descr = db.Column(db.String(128))
    end_date = db.Column(db.DateTime)
    leagues = db.relationship('Leagues', back_populates='rounds')
    songs = db.relationship('Songs', back_populates='rounds')
    votes = db.relationship('Votes', back_populates='rounds')

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
    video_id = db.Column(db.String(32))
    title = db.Column(db.String(512))
    thumbnail = db.Column(db.String(256))
    leagues = db.relationship('Leagues', back_populates='songs')
    user = db.relationship('Users', back_populates='songs')
    rounds = db.relationship('Rounds', back_populates='songs')
    votes = db.relationship('Votes', back_populates='songs')

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
    leagues = db.relationship('Leagues', back_populates='votes')
    rounds = db.relationship('Rounds', back_populates='votes')
    songs = db.relationship('Songs', back_populates='votes')
    user = db.relationship('Users', back_populates='votes')

    def __repr__(self):
        return f'<Song Id {self.song_id}\tVotes {self.votes}>'

@dataclass
class LeagueStandings():
    name: str
    username: str
    votes: int = 0

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
    now = datetime.utcnow()
    league_id = request.args.get('id', 0, type=int)
    if league_id == 0:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    league = Leagues.query.get(league_id)
    if not league:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    league_status = 'ENDED' if now > league.end_date else 'RUNNING'
    rounds = Rounds.query.filter_by(league_id=league_id).order_by(Rounds.end_date.asc())
    add_button = False
    am_a_member = False
    actions = {r.id: ''  for r in rounds}
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        if request.method == 'GET' and request.args.get('submit', None):
            member = LeagueMembers(league_id=league_id, user_id=user_id)
            db.session.add(member)
            db.session.commit()
            flash("You've been added to this league successfully. Start submitting to the next open round.")
        else:
            join_cut_off_date = league.end_date - timedelta(days=league.vote_days)
            too_late = True if now > join_cut_off_date else False
        # verify league membership status
        am_a_member = LeagueMembers.query.filter_by(league_id=league_id).filter_by(user_id=user_id).first()
        add_button = False if am_a_member or too_late else True
        if am_a_member:
            for round_data in rounds:
                round_status = get_round_status(league.submit_days, league.vote_days, round_data.end_date, round_data.id)
                if round_status == 0:
                    action = 'ENDED'
                elif round_status == 1:
                    action = Markup('<b>VOTE&nbsp;NOW</b>')
                elif round_status == 2:
                    action = Markup('<b>SUBMIT&nbsp;NOW</b>')
                elif round_status == 3:
                    # submitted already
                    action = Markup('<b>YOU SUBMITTED</b>')
                elif round_status == 4:
                    # voted already
                    action = Markup('<b>YOU VOTED</b>')
                else:
                    # -1
                    action = Markup('NOT&nbsp;STARTED')
                actions[round_data.id] = action
    return render_template('league.html', title='View / Join this Music League', id=league_id, league=league, rounds=rounds, status=league_status, button=add_button, member=am_a_member, actions=actions)


@app.route('/standings', methods=['GET'])
@login_required
def standings():
    """View current league standings (total points for each member)."""
    standings_data = []
    now = datetime.utcnow()
    league_id = request.args.get('id', 0, type=int)
    if league_id == 0:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    league = Leagues.query.get(league_id)
    if not league:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    league_status = Markup('<b>ENDED</b>') if now > league.end_date else 'RUNNING'
    league_members_data = league.members
    votes = league.votes
    songs = league.songs
    for user in league_members_data:
        name = user.user.name
        username = user.user.username
        user_id = user.user.id
        user_votes = [0]
        for song in songs:
            if song.user_id != user_id:
                continue
            user_votes += [vote.votes for vote in votes if vote.song_id == song.id]
        user_data = LeagueStandings(
            name=name,
            username=username,
            votes=sum(user_votes)
        )
        standings_data.append(user_data)
    # sort by total points
    sorted_standings = sorted(standings_data, key=lambda x: x.votes)
    return render_template('standings.html', title='View League Standings', league_data=league, status=league_status, end_date=league.end_date, data=standings_data)


@app.route('/round', methods=['GET', 'POST'])
@login_required
def round_():
    """Round details."""
    user_id = current_user.get_id()
    round_id = request.args.get('id', 0, type=int)
    if round_id == 0:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    round_data = Rounds.query.get(round_id)
    if not round_data:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    league_id = round_data.league_id
    league = Leagues.query.get(league_id)
    if not league:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    # verify league membership status
    am_a_member = LeagueMembers.query.filter_by(league_id=league_id).filter_by(user_id=user_id).first()
    if not am_a_member:
        flash('Not a member of the league, you cannot view round data', 'error')
        return redirect(url_for('leagues'))
    round_status = get_round_status(league.submit_days, league.vote_days, round_data.end_date, round_id)
    if round_status == 0:
        # ended
        songs = Songs.query.filter_by(league_id=league_id).filter_by(round_id=round_id).order_by(Songs.id)
        votes = Votes.query.filter_by(league_id=league_id).filter_by(round_id=round_id).order_by(Votes.vote_date)
    elif round_status == 1:
        # vote
        return redirect(url_for('vote', id=round_id))
    elif round_status == 2:
        # submit song
        return redirect(url_for('submit_song', id=league_id, round=round_id, user=user_id))
    elif round_status in [3, 4]:
        # already submitted or already voted
        pass
    else:
        # not started, or invalid status provided
        flash('The selected round has not yet started', 'error')
        return redirect(url_for('league', id=league_id))
    return render_template('round.html', title='View Round', status=round_status, round_data=round_data)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new league."""
    form = CreateLeagueForm()
    if form.validate_on_submit():
        user_id = current_user.get_id()
        round_days = int(form.submit_days.data) + int(form.vote_days.data)
        total_days = round_days * int(form.round_count.data)
        league = Leagues(name=form.name.data, submit_days=form.submit_days.data, vote_days=form.vote_days.data, descr=form.descr.data, upvotes=form.upvotes.data, downvotes=form.downvotes.data, round_count=form.round_count.data, owner_id=user_id)
        league.set_end_date(form.submit_days.data, form.vote_days.data, form.round_count.data)
        db.session.add(league)
        db.session.commit()
        flash_msg = Markup(f'Congratulations {current_user.name}! <br>You have created a new league called <b>{form.name.data}</b> which will close in {total_days} days')
        flash(flash_msg)
        add_rounds = url_for('add_rounds', league_id=league.id, round_count=form.round_count.data, round_days=round_days)
        return redirect(add_rounds)
    return render_template('create.html', title='Create a new Music League', form=form)


@app.route('/add_rounds', methods=['GET', 'POST'])
@login_required
def add_rounds():
    """Add rounds to the new league."""
    league_id = request.args.get('league_id', 0, type=int)
    round_count = request.args.get('round_count', 0, type=int)
    round_days = request.args.get('round_days', 0, type=int)
    if league_id == 0 or round_count == 0 or round_days == 0:
        flash('Invalid league specified', 'error')
        return redirect(url_for('leagues'))
    form = AddRoundsForm()
    if form.validate_on_submit():
        now = datetime.utcnow()
        for day, round_data in enumerate(form.data['rounds'], start=1):
            days = round_days * day
            end_date = now + timedelta(days=days)
            round_record = Rounds(league_id=league_id, name=round_data['name'], descr=round_data['descr'], end_date=end_date)
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


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_song():
    """Submit a song to a round."""
    user_id = current_user.get_id()
    user__id = request.args.get('user', 0, type=int)
    if int(user_id) != user__id:
        flash('Invalid user', 'error')
        return redirect(url_for('leagues'))
    round_id = request.args.get('round', 0, type=int)
    if round_id == 0:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    league_id = request.args.get('id', 0, type=int)
    if league_id == 0:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    form = SubmitSongForm(user=user_id, round=round_id, league=league_id)
    if form.validate_on_submit():
        songs = Songs.query.filter_by(round_id=round_id).filter_by(song_url=form.song_url.data).first()
        if songs:
            flash(f'Someone else has already submitted this song ( {form.song_url.data} )')
            return redirect(url_for('submit_song', id=league_id, round=round_id, user=user_id))
        song_data = get_yt_song_data(form.song_url.data)
        if not song_data:
            flash(f'Invalid youtube song link ( {form.song_url.data} )')
            return redirect(url_for('submit_song', id=league_id, round=round_id, user=user_id))
        new_song = Songs(league_id=league_id, user_id=user_id, round_id=round_id, song_url=form.song_url.data, descr=form.descr.data, video_id=song_data['video_id'], title=song_data['title'], thumbnail=song_data['thumbnail'])
        db.session.add(new_song)
        db.session.commit()
        flash(f"Thanks for submitting the song ( {song_data['title']} ) for this round")
        return redirect(url_for('round_', id=round_id))
    return render_template('submit.html', title='Submit a Song', form=form)


@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    """Vote for songs in the league/round."""
    user_id = current_user.get_id()
    round_id = request.args.get('id', 0, type=int)
    if round_id == 0:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    round_data = Rounds.query.get(round_id)
    if not round_data:
        flash('Invalid round selected', 'error')
        return redirect(url_for('leagues'))
    league_id = round_data.league_id
    league = Leagues.query.get(league_id)
    if not league:
        flash('Invalid league selected', 'error')
        return redirect(url_for('leagues'))
    # verify league membership status
    am_a_member = LeagueMembers.query.filter_by(league_id=league_id).filter_by(user_id=user_id).first()
    if not am_a_member:
        flash('Not a member of the league, you cannot view round data', 'error')
        return redirect(url_for('leagues'))
    songs = Songs.query.filter_by(round_id=round_id).filter_by(league_id=league_id).filter(Users.id!=user_id)
    if not songs:
        flash('Zero songs to vote on in this round', 'error')
        return redirect(url_for('round_', id=round_id))
    form = VoteForm()
    if request.method == 'POST' and form.is_submitted():
        total_votes = 0
        song_ids = [i.id for i in songs.all()]
        for song_id in song_ids:
            votes = request.form.get(f'vote-{song_id}', type=int)
            total_votes += votes
            comment = request.form.get(f'comment-{song_id}', '')
            vote = Votes(song_id=song_id, league_id=league_id, round_id=round_id, user_id=user_id, votes=votes, comment=comment)
            db.session.add(vote)
        if total_votes > league.upvotes or total_votes < -abs(league.downvotes):
            # enforce per round vote count limits
            db.session.rollback()
            flash(f'Total votes must not be greater than {league.upvotes} or less than -{league.downvotes}', 'error')
        else:    
            db.session.commit()
            flash(f'Thanks for voting in round: {round_data.name}')
        return redirect(url_for('round_', id=round_id))
    return render_template('vote.html', title='Vote for songs', songs=songs.all())


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """Send email."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def get_round_status(submit_days, vote_days, round_end_date, round_id):
    """Determine the status of specified round, based on date data.

    returns integer value indicating status:
        -1 = not started
        0 = ended/finished
        1 = voting in progress
        2 = submissions in progress
        3 = already submitted a song
        4 = already voted
    """
    user_id = current_user.get_id()
    round_status = -1
    now = datetime.utcnow()
    round_days_total = submit_days + vote_days
    vote_start_date = round_end_date - timedelta(days=vote_days)
    submit_start_date = round_end_date - timedelta(days=round_days_total)
    if now >= round_end_date:
        round_status = 0
    elif now >= vote_start_date and now < round_end_date:
        voted = has_user_voted(user_id, round_id)
        if voted:
            round_status = 4
        else:
            round_status = 1
    elif now >= submit_start_date and now < vote_start_date:
        submitted = is_song_submitted(user_id, round_id)
        if submitted:
            round_status = 3
        else:
            round_status = 2
    return round_status


def is_song_submitted(user_id, round_id):
    """Determine whether this user already submitted a song for this round."""
    is_submitted = False
    songs = Songs.query.filter_by(user_id=user_id).filter_by(round_id=round_id).first()
    if songs:
        is_submitted = True
    return is_submitted


def has_user_voted(user_id, round_id):
    """Determine whether this user has already voted in this round."""
    has_voted = False
    votes = Votes.query.filter_by(user_id=user_id).filter_by(round_id=round_id).first()
    if votes:
        has_voted = True
    return has_voted


def get_yt_song_data(song_url):
    """Query youtube API for song data."""
    song_data = {}
    try:
        # get API client
        yt = youtube_api.YouTubeDataAPI(app.config['YT_API_KEY'])
    except ValueError:
        app.logger.error('Invalid youtube API key')
        return song_data
    # parse song_url
    parsed = urlparse(song_url)
    if parsed.netloc != 'www.youtube.com':
        app.logger.info(f'Invalid song_url specified ( {song_url} )')
        return song_data
    video_id = parsed.query.replace('v=', '')
    try:
        data = yt.get_video_metadata(video_id)
    except TypeError as err:
        app.logger.warning(f'Invalid video Id specified ( {song_url} )')
        return song_data
    if not data:
        app.logger.warning(f'Invalid video Id specified ( {song_url} )')
        return song_data
    song_data['video_id'] = data['video_id']
    song_data['title'] = data['video_title']
    song_data['thumbnail'] = data['video_thumbnail']
    return song_data


# used by 'flask shell' to setup query context
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Icons': Icons, 'Leagues': Leagues, 'LeagueMembers':LeagueMembers, 'Rounds': Rounds, 'Songs': Songs, 'Votes': Votes}


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
