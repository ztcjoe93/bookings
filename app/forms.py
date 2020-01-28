from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, DateTimeField, HiddenField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, ValidationError, NumberRange, Optional
from app.models import db, User, Booking, Event, Location
from wtforms.fields.html5 import DateField, DateTimeLocalField
from wtforms.widgets import HiddenInput, TextArea
import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log in')

class RegistrationForm(FlaskForm):
    username = StringField('Username', [DataRequired()])
    email = StringField('Email', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])
    password_re = PasswordField('Re-enter Password', [DataRequired(), EqualTo('password', message="Passwords do not match")])
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        valid = User.query.filter_by(username=username.data).first()
        if valid is not None:
            raise ValidationError('Please select a different username.')

    def validate_email(self, email):
        valid = User.query.filter_by(email=email.data).first()
        if valid is not None:
            raise ValidationError('Please select a different email.')

class EventForm(FlaskForm):
    name = StringField('Event Name', [DataRequired()])
    capacity = IntegerField('Capacity', [DataRequired(), NumberRange(min=1)])
    start_date = DateTimeLocalField('Start Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeLocalField('End Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    location = SelectField('Location', choices=[], coerce=int)
    img_name = FileField('File') 
    description = StringField('Description', widget=TextArea(), validators=[Optional()])
    submit = SubmitField('Create')

    def validate_name(self, name):
        valid = Event.query.filter_by(name=name.data).first()
        if valid is not None:
            raise ValidationError('Event with name exists.')

class LocationForm(FlaskForm):
    name = StringField('Location Name', [InputRequired()])
    address = StringField('Address Name', widget=TextArea(), validators=[Optional()])
    submit = SubmitField('Create')

class BookingForm(FlaskForm):
    amount = IntegerField('Number of Tickets', [DataRequired()])
    submit = SubmitField('Book now')

class AdminRemoveForm(FlaskForm):
    model_type = HiddenField()
    event_id = HiddenField(validators=[Optional()])
    location_id = HiddenField(validators=[Optional()])

class RemoveForm(FlaskForm):
    book_id = HiddenField()
    event_id = HiddenField()
    qt = IntegerField(widget=HiddenInput())
    md_qt = IntegerField("Modified Quantity", validators=[Optional()])

    def validate_md_qt(self, md_qt):
        if md_qt.data == 0:
            raise ValidationError('Kindly utilize the x button if you wish to cancel your booking.')
        elif md_qt.data < 0 or md_qt.data >= self.qt.data:
            raise ValidationError('Kindly enter a valid input for the number of tickets you wish to adjust to.')
            

class UpdateForm(FlaskForm):
    org_name = StringField(widget=HiddenInput())
    name = StringField('Event Name', validators=[Optional()])
    capacity = IntegerField('Current Capacity', widget=HiddenInput())
    org_cap = IntegerField(widget=HiddenInput())
    max_cap = IntegerField('Max Capacity', validators=[Optional(), NumberRange(min=1)])
    start_date = DateTimeLocalField('Start Date/Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    org_start_date = DateTimeLocalField(widget=HiddenInput())
    end_date = DateTimeLocalField('End Date/Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    org_end_date = DateTimeLocalField(widget=HiddenInput())
    img_name = FileField('Image')
    description = TextAreaField('Description')
    submit = SubmitField('Update')

    def validate_max_cap(self, max_cap):
        if(self.capacity.data + (max_cap.data - self.org_cap.data) < 0):
            raise ValidationError('Not enough capacity for reduction.')

    def validate_name(self, name):
        if name is not "":
            valid = Event.query.filter_by(name=name.data).first()
            if valid is not None:
                raise ValidationError('Event with name exists.')

    def validate_start_date(self, start_date):
        if start_date is not None:
            ctime = self.end_date.data if self.end_date.data is not None else self.org_end_date.data
            if(ctime - start_date.data < datetime.timedelta(0, 0, 0)):
                raise ValidationError('Event Start Time is after End Time')

    def validate_end_date(self, end_date):
        if end_date is not None:
            ctime = self.start_date.data if self.start_date.data is not None else self.org_start_date.data
            if(end_date.data - ctime < datetime.timedelta(0, 0, 0)):
                raise ValidationError('Event End Time is before Start Time')

class UpdateLForm(FlaskForm):
    org_address = StringField(widget=HiddenInput())
    address = StringField('Address', validators=[Optional()])
    
    submit = SubmitField("Update")

class PasswordRequestForm(FlaskForm):
    email = StringField('Please enter your Email Address', validators=[InputRequired(), Email()])
    submit = SubmitField('Submit')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired()])
    password_re = PasswordField('Re-enter Password', validators=[InputRequired(), EqualTo('password', 'Password does not match')])
    submit = SubmitField('Submit')
