from flask import redirect, url_for
from flask.ext import admin
from flask.ext.admin import expose
from flask.ext.admin.contrib import sqla
from flask.ext.admin.form.fields import Select2Field
from flask.ext.admin.form import FormOpts
from flask.ext.login import current_user
from flask.ext.admin.actions import action
from wtforms.fields import SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired
from flask_wtf import Form as flask_wtf__Form
from datetime import datetime, timedelta


from cbbpoll import app, db
from models import User, Team, Ballot, Poll, Vote, VoterEvent

def teamChoices():
    try:
        teams = Team.query.all()
        choices = [('-1', '')]
        for team in teams:
            choice = ((team.id, str(team)))
            choices.append(choice)
    except Exception:
        choices = None
    return choices

class AdminModelView(sqla.ModelView):
    form_base_class = flask_wtf__Form
    def is_accessible(self):
        return not current_user.is_anonymous() and current_user.is_admin()

class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if current_user.is_anonymous() or not current_user.is_admin():
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['nickname', 'email', 'emailConfirmed', 'role', 'team', 'emailReminders', 'pmReminders']
    column_list = ['id', 'nickname', 'email', 'emailConfirmed', 'role', 'is_pollster', 'team', 'team.conference']
    column_searchable_list = ('nickname', 'email')
    column_filters = ('team.conference', 'role')
    form_overrides = dict(role=Select2Field)
    form_args = dict(
     #Pass the choices to the `SelectField`
        role=dict(
        choices=[('u', 'user'), ('p', 'pollster'), ('a', 'admin')]
        ))

    @action('promote', 'Make Pollster', 'Are you sure you want to set the selected users to pollsters?')
    def action_promote(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.is_pollster = True
            db.session.add(user)
            db.session.commit()

    @action('demote', 'Make User', 'Are you sure you want to revoke the selected users\' voter status?')
    def action_demote(self, ids):
        for Id in ids:
            user = User.query.get(Id)
            user.is_pollster = False
            db.session.add(user)
            db.session.commit()

class TeamAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['full_name', 'short_name', 'nickname', 'conference', 'flair', 'png_name']
    column_list = ['id', 'full_name', 'short_name', 'nickname', 'conference', 'flair', 'png_name']
    column_searchable_list = ('full_name', 'short_name', 'nickname', 'conference')

class PollAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['season', 'week', 'openTime', 'closeTime', 'ballots']
    column_list = ['id', 'season', 'week', 'openTime', 'closeTime', 'ballots']

    @action('close', 'Close Poll', 'This will snap the poll at the current time.  Continue?')
    def action_close(self, id):
        poll = Poll.query.get(id)
        poll.closeTime = datetime.utcnow()
        db.session.add(poll)
        db.session.commit()

    @action('open', 'Open Poll', 'This will cause the poll to close this time tomorrow.  Continue?')
    def action_open(self, id):
        poll = Poll.query.get(id)
        poll.closeTime = datetime.utcnow() + timedelta(days=1)
        db.session.add(poll)
        db.session.commit()

class VoteAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['ballot_id', 'rank', 'team_id', 'reason']
    column_list = ['id', 'ballot_id', 'rank', 'team', 'reason']
    form_overrides = dict(team_id=Select2Field)
    form_args = dict(
        team_id=dict(choices = teamChoices(),
        validators=[InputRequired(message="You must select a team.")],
        coerce=int
    ))

class BallotAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['user_id', 'poll_id']
    column_list = ['id', 'user_id', 'poll_id', 'updated', 'votes', 'is_provisional']

class VoterEventAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['user_id', 'is_voter', 'timestamp']
    column_list = ['id', 'user_id', 'user.nickname', 'is_voter', 'timestamp']
    column_default_sort = ('timestamp', True)


# Create admin
admin = admin.Admin(app, 'User Poll Control Panel', index_view=MyAdminIndexView(endpoint="admin"))
admin.add_view(UserAdmin(User, db.session))
admin.add_view(TeamAdmin(Team, db.session))
admin.add_view(PollAdmin(Poll, db.session))
admin.add_view(BallotAdmin(Ballot, db.session))
admin.add_view(VoteAdmin(Vote, db.session))
admin.add_view(VoterEventAdmin(VoterEvent, db.session))
