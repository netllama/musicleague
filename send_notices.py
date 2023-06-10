#!/usr/bin/env python
"""Used to generate cron driven slack & email notifications"""

from dataclasses import dataclass
import datetime
import os
import random

from dotenv import load_dotenv

load_dotenv(f'{os.path.dirname(os.path.realpath(__file__))}/.flaskenv')  # needed by musicleague module imports
from flask import render_template
import html2text
from musicleague import app, db, get_round_status, send_email, LeagueMembers, Leagues, Rounds
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


app.config['PREFERRED_URL_SCHEME'] = os.environ['PREFERRED_URL_SCHEME']
app.config['SERVER_NAME'] = os.environ['SERVER_NAME']


@dataclass
class EmailStateData:
    id: int
    db: str
    status_str: str


def make_emails():
    """Find rounds that are ready for submission, voting or ended, and send out notifications."""
    base_url = f"{app.config['PREFERRED_URL_SCHEME']}://{app.config['SERVER_NAME']}{app.config['APP_WEB_PATH']}"
    running_email_states = {
        1: EmailStateData(id=1, db='vote_email', status_str='submit your vote'),
        2: EmailStateData(id=2, db='submit_email', status_str='submit your song'),
    }
    end_states = {
        0: EmailStateData(id=0, db='end_email', status_str='view round voting results'),
    }
    now = datetime.datetime.utcnow()
    # get league rounds which have not finished yet, for running_email_states
    unfinished_leagues = Leagues.query.filter(Leagues.end_date >= now).all()
    for league in unfinished_leagues:
        url = f'{base_url}/league?id={league.id}'
        members = LeagueMembers.query.filter_by(league_id=league.id).all()
        if not members:
            app.logger.warning(f'Zero members in league {league.name} ({league.id})')
            continue
        unfinished_rounds = Rounds.query.filter_by(league_id=league.id).filter(Rounds.end_date >= now).all()
        for round_data in unfinished_rounds:
            league_round_id = f'league = "{league.name}" round = "{round_data.name}"'
            for status_id, status_data in running_email_states.items():
                if getattr(round_data, status_data.db):
                    # email already generated
                    continue
                email_recipients = []
                email_subject = f'[Music League: {league.name[:20]}] its time to {status_data.status_str} !'
                for member in members:
                    round_status = get_round_status(
                        league.submit_days, league.vote_days, round_data.end_date, round_data.id, member.user.id
                    )
                    if round_status == status_id:
                        # collect members who need to receive this status email
                        email_recipients.append(member.user.email)
                # generate emails
                for recipient in email_recipients:
                    try:
                        generate_email(email_subject, [recipient], status_data.status_str, url)
                    except Exception as err:
                        app.logger.error(
                            f'Failed to generate {status_data.db} email for {league_round_id} {recipient} due to error:\t{err}'
                        )
                        continue
                    setattr(round_data, status_data.db, True)
                if len(email_recipients):
                    db.session.commit()
                    app.logger.info(f'Sent {len(email_recipients)} "{status_data.db}" emails for {league_round_id}')
                    # generate slack message
                    create_slack_msg(url, email_subject)
    # get league rounds which have just finished, for end_states
    unfinished_rounds = Rounds.query.filter_by(end_email=False).filter(Rounds.end_date <= now).all()
    for round_ in unfinished_rounds:
        league_id = round_.league_id
        url = f'{base_url}/round?id={round_.id}'
        members = LeagueMembers.query.filter_by(league_id=league_id).all()
        if not members:
            app.logger.warning(f'Zero members in league {round_.leagues.name} ({league_id})')
            continue
        league_round_id = f'league = "{round_.leagues.name}" round = "{round_.name}"'
        for status_id, status_data in end_states.items():
            email_recipients = [m.user.email for m in members]
            email_subject = f'[Music League: {round_.leagues.name[:20]}] its time to {status_data.status_str} !'
            # generate emails
            for recipient in email_recipients:
                try:
                    generate_email(email_subject, [recipient], status_data.status_str, url)
                except Exception as err:
                    app.logger.error(
                        f'Failed to generate {status_data.db} email for {league_round_id} {recipient} due to error:\t{err}'
                    )
                    continue
                setattr(round_, status_data.db, True)
            if len(email_recipients):
                db.session.commit()
                app.logger.info(f'Sent {len(email_recipients)} "{status_data.db}" emails for {league_round_id}')


def create_slack_msg(url, base_msg):
    """Generate announcement to slack channel."""
    if not os.environ.get('SLACK_CHANNEL') or not os.environ.get('SLACK_BOT_TOKEN'):
        # no slack channel or bot token configured
        return
    emojis = [
        ':catflix:',
        ':llama:',
        ':music_cat:',
        ':foosball:',
        ':shira-model:',
        ':gemma-sky:',
        ':kakuk-sfw:',
        ':flynnie:',
        ':kaleo-party:',
        ':ellie:',
        ':pretz-look:',
        ':alien-chips:',
        ':frosty:',
        ':meimei:',
        ':mystery_cat:',
    ]
    token = os.environ.get('SLACK_BOT_TOKEN')
    channel = os.environ.get('SLACK_CHANNEL')
    msg = f':tada: {base_msg} {" ".join(random.sample(emojis, k=3))} {url}'
    try:
        client = WebClient(token=token)
        client.chat_postMessage(channel=channel, text=msg)
    except SlackApiError as err:
        app.logger.error(f'Failed to post to slack channel {channel} "{msg}" due to error:\t{err}')


def make_email_html_body(status_str, url):
    """Generate HTML email body content."""
    body = render_template('email.html', status=status_str, url=url)
    return body


def generate_email(subject, recipients, status_str, url):
    """Generate emails to specified recipeients.

    subject: (str) email subject
    recipients: (list) list of email recipients (email address strings)
    status_str: (str) status information for the email
    url: (str) league URL
    """
    html_body = make_email_html_body(status_str, url)
    text_body = html2text.html2text(html_body)
    send_email(subject, os.environ['ADMIN_EMAIL'], recipients, text_body, html_body)


if __name__ == '__main__':
    with app.app_context():
        make_emails()
