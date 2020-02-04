from flask import abort, redirect, url_for, render_template, request, make_response, flash, Blueprint, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
from flask import current_app as app
from app.forms import LoginForm, RegistrationForm, BookingForm, PasswordRequestForm, PasswordResetForm
from app.models import db, User, Booking, Event, Location
from app.extensions import mail
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from threading import Thread
from sqlalchemy import and_
import os.path
import json

#blueprint setup
main_panel = Blueprint('main_panel',
			__name__,
			template_folder="templates",
			static_folder="static",
                        url_prefix="/")

@main_panel.route('/')
def main_url():
    return redirect(url_for('main_panel.index'))

@main_panel.route('/index')
def index(username=None):
    if current_user.is_authenticated:
        username = current_user.username
    return render_template('index.html', username=username)

@main_panel.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        f = request.form
       
        qr = []
        if f['eventName']:
            qr.append(Event.name.ilike('%'+f['eventName']+'%'))

        if f['eventEnd'] and f['eventStart'] == "":
            qr.append(Event.end >= f['eventEnd'])
        elif f['eventStart'] and f['eventEnd']:
            qr.append(and_(Event.start <= f['eventStart'], Event.end >= f['eventEnd']))
        elif f['eventStart'] and f['eventEnd'] == "":
            qr.append(and_(Event.start <= f['eventStart'], Event.end >= f['eventStart']))
 
        if f['eventLocation']:
            qr.append(Location.name.ilike('%'+f['eventLocation']+'%'))

        pages = db.session.query(Event) \
                    .join(Location, Location.id==Event.location_id) \
                    .with_entities(Event.id, Event.name, Event.capacity, Event.start, Event.end, Location.name.label('location_name'), Event.img_name, Event.description) \
                    .filter(*qr) \
                    .paginate(max_per_page=5)

    else:
        pages = db.session.query(Event).join(Location, Location.id==Event.location_id).with_entities(Event.id, Event.name, Event.capacity, Event.start, Event.end, Location.name.label('location_name'), Event.img_name, Event.description).paginate(max_per_page=5)

    events = pages.items
    return render_template('events.html', events=events, pagination=pages)

@main_panel.route('/events/<int:event_id>', methods=['GET', 'POST'])
def load_event(event_id):
    data = db.session.query(Event).join(Location, Location.id==Event.location_id).with_entities(Event.id, Event.name, Event.capacity, Event.start, Event.end, Location.name.label('location_name'), Location.address, Event.img_name, Event.description).filter(Event.id==event_id).first()
    if data is None:
        return render_template('error_event.html')
    return render_template('event_id.html', event_id=event_id, data=data)

@main_panel.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@main_panel.route('/mybookings', methods=['GET', 'POST'])
@login_required
def mybookings():
    bookings = db.session.query(Booking).filter(Booking.user_id==current_user.id).join(Event, Event.id==Booking.event_id).with_entities(Booking.id, Booking.event_id, Booking.quantity, Event.name).all()

    if request.method == 'POST':
        f = request.form

        booking = db.session.query(Booking).filter(Booking.id == f['booking_id']).first()
        event = db.session.query(Event).filter(Event.id == booking.event_id).first()
        if(f['mod_type'] == 'modify'):
            booking.quantity -= int(f['md_qt'])
            event.capacity += int(f['md_qt'])
            flash("Returned {} tickets for {} event.".format(f['md_qt'], event.name), "info")
            app.logger.info('User ID {} returned {} tickets for Event ID {} at {}'.format(current_user.id, f['md_qt'], event.id, datetime.now()))
        else:
            event.capacity += booking.quantity
            Booking.query.filter(Booking.id == f['booking_id']).delete()
            app.logger.info('User ID {} cancelled Booking ID {} at {}.'.format(current_user.id, booking.id, datetime.now())) 

        db.session.commit()
        return redirect(url_for('main_panel.mybookings'))
    return render_template('mybookings.html', bookings=bookings)

@main_panel.route('/book/<int:event_id>', methods=['GET', 'POST'])
@login_required
def book(event_id):
    data = db.session.query(Event).join(Location, Location.id==Event.location_id).with_entities(Event.name, Event.capacity, Event.start, Event.end, Location.name.label('location_name'), Location.address, Event.img_name).filter(Event.id==event_id).first()

    ticket_amt = [(i,i) for i in range(1, data.capacity+1)]
    form = BookingForm()
    form.amount.choices = ticket_amt

    if data is None:
        return render_template('error_event.html')
    if form.validate_on_submit():
        event = Event.query.get(event_id)
        event.capacity -= form.amount.data
        booking = Booking(user_id=current_user.id, 
                        event_id=event_id, 
                        quantity=form.amount.data,
                        book_time=datetime.utcnow(),
                        last_modified=datetime.utcnow())
        db.session.add(booking)
        db.session.commit()
        app.logger.info('User ID {} has booked {} tickets (Booking ID {}) for Event ID {} at {}.'.format(booking.user_id, booking.quantity, booking.id, booking.event_id, datetime.now()))
        flash('Successfully purchased {} tickets for {}'.format(form.amount.data, data.name), "info") 
        return redirect(url_for('main_panel.events'))
    return render_template('book.html', event_id=event_id, data=data, form=form)

@main_panel.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_panel.index'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_pwd(form.password.data):
            flash('Wrong username/password', 'error')
            return redirect(url_for('main_panel.login'))

        if user.verification == True:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                flash('Successfully logged in!', 'info')
                app.logger.info('User ID {} logged in at {}'.format(user.id, datetime.now()))
                return redirect(url_for('main_panel.index'))
            else:
                return redirect(next_page)
        else:
            flash("Account not verified yet, please check your email.", "error")
            return redirect(url_for('main_panel.login'))

    return render_template('login.html', form=form)

@main_panel.route('/logout')
def logout():
    app.logger.info('User ID {} logged out at {}.'.format(current_user.id, datetime.now()))
    logout_user()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('main_panel.index'))

@main_panel.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data)
        user.set_pwd(form.password.data)
        db.session.add(user)
        db.session.commit()
        app.logger.info('User ID {} created at {}'.format(user.id, datetime.now()))
        token = ts.dumps(user.email, salt='verify-email')
        verify_url = url_for('main_panel.verify', token=token, _external=True)

        html = render_template('email_verify.html', verify_url=verify_url)
        msg = Message(subject="Email verification for {}".format(user.username),
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[user.email],
                    html=html)

        Thread(target=send_email, args=(app._get_current_object(), msg)).start()

        flash("A verification email has been sent, kindly check your email.", "info")
        app.logger.info('Verification email thread started for User ID {} at {}'.format(user.id, datetime.now()))
        return redirect(url_for('main_panel.login'))
    return render_template('register.html', form=form)

@main_panel.route('/verify/<token>', methods=['GET', 'POST'])
def verify(token): 
    ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    email = ts.loads(token, salt="verify-email", max_age=86400) 

    user = User.query.filter_by(email=email).first()
    user.verification = True
    db.session.commit()

    flash("Account successfully verified.", "info") 
    app.logger.info('User ID {} verified at {}'.format(user.id, datetime.now()))

    return redirect(url_for('main_panel.login'))


def send_email(app, msg):
    with app.app_context():
        mail.send(msg)
        app.logger.info('Email has been sent at {}'.format(datetime.now()))


@main_panel.route('/reset', methods=['GET', 'POST'])
def reset():
    form = PasswordRequestForm()
    ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    if form.validate_on_submit():
        user = User.query.filter_by(email=request.form['email']).first()
        if user is not None:
            token = ts.dumps(user.email, salt='recover-pw')
            recover_url = url_for('main_panel.reset_token', token=token, _external=True)
            html = render_template('email_pw_reset.html', recover_url=recover_url)
            msg = Message(subject="Password Reset request for {}".format(user.username),
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[user.email],
                        html=html)

            Thread(target=send_email, args=(app._get_current_object(), msg)).start()

        flash("Password reset requested, kindly check your email.", "info") 
        app.logger.info('User ID {} requested for password reset at {}'.format(current_user.id, datetime.now()))
        return redirect(url_for('main_panel.login'))
    return render_template('reset.html', form=form)

@main_panel.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    ts = URLSafeTimedSerializer(app.config.get('SECRET_KEY'))
    email = ts.loads(token, salt="recover-pw", max_age=86400) 
    form = PasswordResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        user.set_pwd(form.password.data)
        db.session.commit()
        app.logger.info('Password reset completed for User ID {} at {}'.format(current_user.id, datetime.now()))
        return redirect(url_for('main_panel.login'))

    return render_template('reset_token.html', form=form, token=token, email=email)

@main_panel.route('/api', methods=['GET'])
def home():
    return '\
        <html>\
            events<br>\
            - ?name : double wildcards search, event name that contains string<br>\
            - ?loc : double wildcards search for location name, search based on id for first result<br><br>\
            locations<br>\
            - ?name : double wildcards search, location name that contains string<br>\
            - ?addr : double wildcards search, address name that contains string\
        </html>\
    ' 

@main_panel.route('/api/v1/resources/events', methods=['GET'])
def api_events():
    params = request.args 
    name = params.get('name')
    loc = params.get('loc')
    qr = []

    if name:
        qr.append(Event.name.ilike("%"+name+"%"))
    if loc:
        the_loc = Location.query.filter(Location.name.ilike("%"+loc+"%")).first()
        qr.append(Event.location_id == the_loc.id)

    dataset = Event.query.filter(*qr).all()

    return json.dumps([data.as_dict() for data in dataset], indent=4, sort_keys=True)

@main_panel.route('/api/v1/resources/locations', methods=['GET'])
def api_locations():
    params = request.args 
    name = params.get('name')
    addr = params.get('addr')
    
    qr = []

    if name:
        qr.append(Location.name.ilike("%"+name+"%"))
    if addr:
        qr.append(Location.address.ilike("%"+addr+"%"))
        
    dataset = Location.query.filter(*qr).all()

    return json.dumps([data.as_dict() for data in dataset], indent=4, sort_keys=True)
