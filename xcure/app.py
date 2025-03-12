from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db, bcrypt, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = 'excure2025' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  

from flask_migrate import Migrate

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    from models import Account
    return Account.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/register/doctor",methods=["GET","POST"])
def doctor_register():
    from forms import DoctorSignupForm
    form=DoctorSignupForm()
    if request.method == "POST":
        if form.validate_on_submit():
            validated_data = form.data
            doctor = Account(
                first_name=validated_data.get("first_name"),
                last_name=validated_data.get("last_name"),
                email=validated_data.get("email"),
                user_role="doctor"
            )
            doctor.set_password(validated_data.get("password"))
            db.session.add(doctor)
            try:
                db.session.commit()
                flash(f"Doctor Registration Successful. Doctor ID: {doctor.user_id}", "success")
                return redirect(url_for('login_page'))
            except IntegrityError:
                db.session.rollback() 
                flash("An error occurred. Please try again.", "danger")
            return redirect(url_for('login_page'))
    return render_template('signup.html', form=form)

@app.route('/login',methods=["GET","POST"])
def login_page():
    from forms import DoctorLoginForm, PatientLoginForm
    doctor_form = DoctorLoginForm()
    patient_form = PatientLoginForm()
    if request.method == "POST":
        if request.form.get("user_type") == "doctor":  
            if doctor_form.validate_on_submit():
                doctor_id = doctor_form.doctor_id.data
                password = doctor_form.password.data
                doctor = Account.query.filter_by(user_id=doctor_id, user_role="doctor").first()
                if doctor and doctor.check_password(password):
                    login_user(doctor)  
                    flash("Doctor login successful!", "success")
                    return redirect(url_for('doctor_dashboard'))
                else:
                    flash("Invalid Doctor ID or password", "danger")

        elif 'patient_submit' in request.form: 
            print("patient")
            if patient_form.validate_on_submit():
                patient_id = patient_form.patient_id.data

                patient = Account.query.filter_by(user_id=patient_id, user_role="patient").first()
                if patient:
                    login_user(patient)  
                    flash("Patient login successful!", "success")
                    return redirect(url_for('patient_dashboard'))
                else:
                    flash("Invalid Patient ID", "danger")
    return render_template("login.html", doctor_form=doctor_form, patient_form=patient_form)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

@app.route('/search-patient', methods=['GET'])
def search_patient():
    return render_template('doctor_dashboard.html')

@app.route('/edit-patient/<patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    pass

@app.route('/delete-patient/<patient_id>')
def delete_patient(patient_id):
    pass

@app.route('/patient-dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    pass

@app.route('/add-patient', methods=['POST'])
def add_patient():
    pass

@app.route('/view_patient', methods=['GET', 'POST'])
def view_patient():
    pass

if __name__ == '__main__':
    with app.app_context():
        from models import Account, MedicalReport, XRay 
        db.create_all() 
    app.run(debug=True)
