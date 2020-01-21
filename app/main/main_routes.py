from flask import abort, redirect, url_for, render_template, request, make_response, flash, Blueprint, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
from flask import current_app as app
from app.forms import LoginForm, RegistrationForm, BookingForm, RemoveForm, PasswordRequestForm, PasswordResetForm
from app.models import db, User, Booking, Event, Location
from app.extensions import mail
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse
from datetime import datetime
import os.path

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
    print("test")
    return render_template('index.html', username=username)

@main_panel.route('/events')
def events():
    events = db.session.query(Event).join(Location, Location.id==Event.location_id).with_entities(Event.id, Event.name, Event.capacity, Event.start, Event.end, Location.name.label('location_name'), Event.img_name, Event.description).all()
    return render_template('events.html', events=events)

@main_panel.route('/events/<int:event_id>', methods=['GET', 'POST'])
def load_event(event_id):
    data = db.session.query(Event, Location).filter(Event.id==event_id).first()
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
    form = RemoveForm()
    if form.validate_on_submit():
        if form.md_qt.data is not None:
            booking = Booking.query.filter(Booking.id==form.book_id.data).first()
            difference = booking.quantity - form.md_qt.data
            booking.quantity = form.md_qt.data 
            Event.query.get(form.event_id.data).capacity += difference
        else:
            Booking.query.filter(Booking.id==form.book_id.data).delete()
            Event.query.get(form.event_id.data).capacity += form.qt.data
        
        flash("Successfully updated.", "info")
        db.session.commit()
        return redirect(url_for('main_panel.events'))
    return render_template('mybookings.html', bookings=bookings, form=form)

@main_panel.route('/book/<int:event_id>', methods=['GET', 'POST'])
@login_required
def book(event_id):
    data = db.session.query(Event, Location).filter(Event.id==event_id).first()
    form = BookingForm()
    if data is None:
        return render_template('error_event.html')
    if form.validate_on_submit():
        event = Event.query.get(event_id)
        event.capacity -= form.amount.data
        booking = Booking(user_id=current_user.id, 
                        event_id=event_id, 
                        quantity=form.amount.data,
                        book_time=datetime.utcnow())
        db.session.add(booking)
        db.session.commit()
        flash('Successfully purchased {} tickets for {}'.format(form.amount.data, data.Event.name)) 
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
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            flash('Successfully logged in!', 'info')
            return redirect(url_for('main_panel.index'))
        else:
            return redirect(next_page)
    return render_template('login.html', form=form)

@main_panel.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('main_panel.index'))

@main_panel.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data)
        user.set_pwd(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been successfully created at {}".format(user.username, datetime.utcnow()), "info")
        return redirect(url_for('main_panel.login'))
    return render_template('register.html', form=form)

@main_panel.route('/reset', methods=['GET', 'POST'])
def reset():
    form = PasswordRequestForm()
    ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    if form.validate_on_submit():
        user = User.query.filter_by(email=request.form['email']).first()
        if user is not None:
            token = ts.dumps(user.email, salt='recover-pw')
            recover_url = url_for('main_panel.reset_token', token=token)
            html = render_template('email_pw_reset.html', recover_url=recover_url)
            msg = Message(subject="Password reset request for NZR",
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[user.email],
                        html=html)
            mail.send(msg) 
        flash("Password reset requested, kindly check your email.", "info") 
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
        return redirect(url_for('main_panel.login'))

    return render_template('reset_token.html', form=form, token=token)
