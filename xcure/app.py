from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from extensions import db, bcrypt
app = Flask(__name__)
app.secret_key = 'excure2025' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

from flask_migrate import Migrate

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    from models import Account
    return Account.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/register/doctor")
def doctor_register():
    return render_template('')

@app.route('/login')
def login_page():
    from forms import DoctorLoginForm, PatientLoginForm
    doctor_form = DoctorLoginForm()
    patient_form = PatientLoginForm()
    return render_template("login.html", doctor_form=doctor_form, patient_form=patient_form)

@app.route('/login/doctor', methods=["POST"])
def doctor_login():
    from forms import DoctorLoginForm
    doctor_form = DoctorLoginForm()
    if doctor_form.validate_on_submit():
        doctor_id = doctor_form.doctor_id.data
        password = doctor_form.password.data
        # Authenticate doctor (- will do db based auth using sql alchemy
        if doctor_id == "doctor123" and password == "password":
            flash("Doctor login successful!", "success")
            return redirect(url_for("doctor_dashboard"))
        else:
            flash("Invalid Doctor ID or password", "danger")

    return redirect(url_for("login_page"))

@app.route('/login/patient',methods=["POST"])
def patient_login():
    from forms import PatientLoginForm
    patient_form = PatientLoginForm()
    if patient_form.validate_on_submit():
        doctor_id = patient_form.doctor_id.data
        password = patient_form.password.data
        # Authenticate patient (- will do db based auth using sql alchemy
        if doctor_id == "doctor123" and password == "password":
            flash("Doctor login successful!", "success")
            return redirect(url_for("doctor_dashboard"))
        else:
            flash("Invalid Doctor ID or password", "danger")
    return redirect(url_for("login_page")) 

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

@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    pass

@app.route('/add-patient', methods=['POST'])
def add_patient():
    pass

@app.route('/view_patient', methods=['GET', 'POST'])
def view_patient():
    pass

if __name__ == '__main__':
    app.run(debug=True)
