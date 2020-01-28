import logging
from flask import Blueprint, render_template, redirect, url_for, flash, make_response, request
from flask import current_app as app
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message, Mail
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from sqlalchemy import inspect
from app.models import User, Booking, Event, Location
from app.forms import EventForm, UpdateForm, UpdateLForm, AdminRemoveForm, LocationForm
from app.extensions import mail, login_manager, db
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
        app.logger.info("[Attempt to log in to admin panel by user_id: %s]", user.id)
        return False
    else:
        return True 

@admin_panel.route('/main', methods=['GET'])
@login_required
def main():
    return render_template('/main.html') if validation(current_user)==True else redirect(url_for('main_panel.index'))

@admin_panel.route('/alldata', methods=['GET', 'POST'])
@login_required
def alldata():
    return render_template('/alldata.html') if validation(current_user)==True else redirect(url_for('main_panel.index'))

@admin_panel.route('/alldata/<string:sub_type>', methods=['GET', 'POST'])
@login_required
def alldata_stype(sub_type):
    if sub_type == 'users':
        data = User.query.all()
    elif sub_type == 'bookings':
        data = Booking.query.all()
    elif sub_type == 'events':
        data = Event.query.all()
    elif sub_type == 'locations':
        data = Location.query.all()

    if request.method == 'POST':
        user = User.query.filter(User.id==request.form['idValue']).first()
        print(user.username)
        if request.form['modType'] == "revoke": 
            user.su_rights = False 
        else: 
            user.su_rights = True
        db.session.commit()

        return redirect(url_for('admin_panel.alldata_stype', sub_type='users'))

    return render_template('alldata_stype.html', sub_type=sub_type, data=data)

@admin_panel.route('/event_create', methods=['GET', 'POST'])
@login_required
def event_create():
    form = EventForm()
    form.location.choices = [(location.id, location.name) for location in Location.query.all()]

    if form.validate_on_submit():
        event = Event(name=form.name.data,
                capacity=form.capacity.data,
                max_capacity=form.capacity.data,
                start=form.start_date.data,
                end=form.end_date.data,
                location_id=form.location.data,
                img_name=form.img_name.data.filename,
                description=form.description.data)
       
        file = form.img_name.data

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename);
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.session.add(event)
        db.session.commit()
        return redirect(url_for('admin_panel.alldata_stype', sub_type='events'))

    return render_template('/event_create.html', form=form) if validation(current_user)==True else redirect(url_for('main_panel.index'))


@admin_panel.route('/location_create', methods=['GET', 'POST'])
def location_create():

    form = LocationForm()
    if form.validate_on_submit():
        db.session.add(Location(name=form.name.data, address=form.address.data))
        db.session.commit()
        flash("Successfully created Location: {}".format(form.name.data), 'info')
        return redirect(url_for('admin_panel.alldata_stype', sub_type='locations'))
    
    return render_template('/location_create.html', form=form) if validation(current_user)==True else redirect(url_for('main_panel.index'))

@admin_panel.route('/event_modify', methods=['GET', 'POST'])
def event_modify():
    data = Event.query.all()

    form = AdminRemoveForm()
    form.model_type.data = "event"

    if form.validate_on_submit():
        #check for existing bookings
        if Booking.query.filter(Event.id==form.event_id.data).first() != None:
            flash("existing records, please delete before removal", "error")
        else:
            Event.query.filter(Event.id==form.event_id.data).delete()
            db.session.commit()

        return redirect(url_for('admin_panel.event_modify'))

    return render_template('/modify.html', data=data, form=form) if validation(current_user)==True else redirect(url_for('main_panel.index'))


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
    
    return render_template('event_modify_id.html', form=form, event=event, locations=locations) if validation(current_user)==True else redirect(url_for('main_panel.index'))


@admin_panel.route('/location_modify', methods=['GET', 'POST'])
def location_modify():
    data = Location.query.all()

    form = AdminRemoveForm()
    form.model_type.data = "location"

    if form.validate_on_submit():
        if Event.query.filter(Event.location_id==form.location_id.data).first() != None:
            flash("existing records, please delete before removal", "error")
        else:
            Location.query.filter(Location.id==form.location_id.data).delete()
            db.session.commit()
        
        return redirect(url_for('admin_panel.location_modify'))

    return render_template('/modify.html', data=data, form=form) if validation(current_user)==True else redirect(url_for('main_panel.index'))


@admin_panel.route('/location_modify/<int:location_id>', methods=['GET', 'POST'])
def location_mod(location_id):
    location = Location.query.filter(Location.id==location_id).first()
    form = UpdateLForm()

    if form.validate_on_submit():
        if form.address.data is not "":
            location.address = form.address.data
            db.session.commit()

        return redirect(url_for('admin_panel.location_modify'))

    return render_template('/location_modify_id.html', form=form, location=location) if validation(current_user)==True else redirect(url_for('main_panel.index'))


@admin_panel.route('/message', methods=['GET', 'POST'])
def message():
    if request.method == 'POST':
        content = request.form['message']
        
        msg = Message(subject="Test email from NZR",
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=["zhengtat@gmail.com"],
                        body=content)
        mail.send(msg)

    return render_template('message.html') if validation(current_user)==True else redirect(url_for('main_panel.index'))

