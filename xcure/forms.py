from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, FileField, TextAreaField, IntegerField, EmailField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, Optional
from flask_wtf.file import FileAllowed

class DoctorSignupForm(FlaskForm):
    first_name = StringField(
        "First Name",
        validators=[
            DataRequired(),
            Length(max=100)
        ],
    )
       
    last_name = StringField(
        "Last Name",
        validators=[
            Length(max=100)
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Invalid email format"),
            Length(max=100)
        ],
    )
    
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long"),
            Regexp(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]+$", 
                   message="Password must contain letters and numbers")
        ],
    )
    
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ],
    )
    
    submit = SubmitField("Register")

class DoctorLoginForm(FlaskForm):
    doctor_id = StringField("Doctor ID", validators=[DataRequired(), Length(min=4, max=200)])
    password = PasswordField("Password", validators=[DataRequired()])
    user_type = HiddenField('User Type', default='doctor') 
    submit = SubmitField("Login")

class PatientLoginForm(FlaskForm):
    patient_id = StringField("Patient ID", validators=[DataRequired(), Length(min=3, max=200)])
    user_type = HiddenField('User Type', default='patient') 
    submit = SubmitField("View My Details")

class XRayForm(FlaskForm):
    image = FileField('X-Ray Image', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Upload X-Ray')

class PrescriptionForm(FlaskForm):
    patient_id = IntegerField('Patient ID', validators=[DataRequired()])
    prescription = TextAreaField('Prescription')
    submit = SubmitField('Add Prescription')

class PatientForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[Optional()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    blood_group = SelectField(
        "Blood Group",
        choices=[
            ("A+", "A+"), ("A-", "A-"),
            ("B+", "B+"), ("B-", "B-"),
            ("O+", "O+"), ("O-", "O-"),
            ("AB+", "AB+"), ("AB-", "AB-")
        ],
        validators=[DataRequired()]
    )
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    phone_number = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Regexp(r'^\+?\d{10,15}$', message="Enter a valid phone number.")
        ]
    )
    submit = SubmitField("Add Patient")