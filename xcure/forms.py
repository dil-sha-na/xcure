from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

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
    doctor_id = StringField("Doctor ID", validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class PatientLoginForm(FlaskForm):
    patient_id = StringField("Patient ID", validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField("View My Details")