from flask import Blueprint, render_template, redirect, url_for, flash, make_response, request
from flask import current_app as app
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message, Mail
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app.models import db, User, Booking, Event, Location
from app.forms import EventForm, UpdateForm, UpdateLForm
from app.extensions import mail
import datetime
import os

MODEL_ATTRIBUTES = ['get_id', 'is_active', 'is_anonymous', 'is_authenticated', 'metadata', 'query', 'query_class']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

#blueprint setup
admin_panel = Blueprint('admin_panel',
			__name__,
			static_folder="static",
			template_folder="templates",
			url_prefix='/admin')

def validation(user):
    if user.su_rights == False:
        return make_response(), 404

@admin_panel.route('/main', methods=['GET'])
@login_required
def main():
    validation(current_user)
    return render_template('/main.html')

@admin_panel.route('/alldata', methods=['GET', 'POST'])
@login_required
def alldata():
    validation(current_user)
    users = User.query.all()
    bookings = Booking.query.all()
    events = Event.query.all()
    locations = Location.query.all()

    data_set = [users, bookings, events, locations]

    return render_template('/alldata.html', data_set=data_set) 

@admin_panel.route('/event_create', methods=['GET', 'POST'])
@login_required
def event_create():
    validation(current_user)
    form = EventForm()
    form.location.choices = [(location.id, location.name) for location in Location.query.all()]

    if form.validate_on_submit():
        event = Event(name=form.name.data,
                capacity=form.capacity.data,
                max_capacity=form.capacity.data,
                start=form.start_date.data,
                end=form.end_date.data,
                location_id=form.location.data,
                img_name=form.img_name.data.filename)
       
        file = form.img_name.data

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename);
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.session.add(event)
        db.session.commit()
        return redirect(url_for('admin_panel.main'))

    return render_template('/event_create.html', form=form)

@admin_panel.route('/location_create', methods=['GET', 'POST'])
def location_create():
    validation(current_user)

    if request.method=='POST':
        db.session.add(Location(name=request.form.get("loc_name"),
                                address=request.form.get("address")))
        db.session.commit()
        flash("Successfully created Location: {}".format(request.form.get("loc_name")))
        return redirect(url_for('admin_panel.main'))
    
    return render_template('/location_create.html')

@admin_panel.route('/event_modify', methods=['GET', 'POST'])
def event_modify():
    validation(current_user)
    events = Event.query.all()

    return render_template('/event_modify.html', events=events)

@admin_panel.route('/event_modify/<int:event_id>', methods=['GET', 'POST'])
def event_mod(event_id):
    event = Event.query.filter(Event.id==event_id).first()
    locations = Location.query.all()
    form = UpdateForm()
    form.capacity.data = event.capacity

    form.org_cap.data = event.max_capacity
    form.org_name.data = event.name
    form.org_start_date.data = event.start
    form.org_end_date.data = event.end
    
    if form.validate_on_submit():
        if form.name.data is not "":
            event.name = form.name.data
            flash("Event name changed from {} to {}.".format(form.org_name.data, form.name.data))
        
        if form.max_cap.data is not None:
            event.max_capacity = form.max_cap.data
            difference = form.max_cap.data - form.org_cap.data
            event.capacity = event.capacity + difference
            flash("Max capacity for {} modified from {} to {}.".format(event.name, form.org_cap.data, form.max_cap.data), "info")

        if form.start_date.data is not None:
            event.start = form.start_date.data
            flash("Event {} start date modified from {} to {}.".format(event.name, form.org_start_date.data, form.start_date.data), "info")

        if form.end_date.data is not None:
            event.end = form.end_date.data
            flash("Event {} end date modified from {} to {}.".format(event.name, form.org_end_date.data, form.end_date.data), "info")

        if form.img_name.data is not None and event.img_name is not form.img_name.data:  
            file = form.img_name.data

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename);
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                event.img_name = form.img_name.data.filename

        if form.description.data is not None:
            event.description = form.description.data

        db.session.commit()
        return redirect(url_for('admin_panel.event_modify'))
    
    return render_template('event_modify_id.html', form=form, event=event, locations=locations)

@admin_panel.route('/location_modify', methods=['GET'])
def location_modify():
    validation(current_user)
    locations = Location.query.all()
            
    return render_template('/location_modify.html', locations=locations)

@admin_panel.route('/location_modify/<int:location_id>', methods=['GET', 'POST'])
def location_mod(location_id):
    location = Location.query.filter(Location.id==location_id).first()
    form = UpdateLForm()

    if form.validate_on_submit():
        if form.address.data is not "":
            location.address = form.address.data
            db.session.commit()

        return redirect(url_for('admin_panel.location_modify'))

    return render_template('/location_modify_id.html', form=form, location=location)

@admin_panel.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', "error")
            return redirect(request.url)
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', "error")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("Successfully uploaded image.", "info")
            return redirect(url_for('admin_panel.main'))
    return render_template('/upload.html')

@admin_panel.route('/message', methods=['GET', 'POST'])
def message():
   
    if request.method == 'POST':
        content = request.form['message']
        
        msg = Message(subject="Test email from NZR",
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=["zhengtat@gmail.com"],
                        body=content)
        mail.send(msg)

    return render_template('message.html')
