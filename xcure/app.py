from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
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
                    session["doctor_name"] = doctor.first_name +  doctor.last_name
                    flash("Doctor login successful!", "success")
                    return redirect(url_for('doctor_dashboard'))
                else:
                    flash("Invalid Doctor ID or password", "danger")

        else: 
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
    from forms import PatientForm, XRayForm, PrescriptionForm
    patient_form = PatientForm()
    prescription_form = PrescriptionForm()
    xray_form = XRayForm()
    return render_template(
        'doctor_dashboard.html', 
        prescription_form=prescription_form, 
        patient_form=patient_form, 
        xray_form=xray_form
    )

@app.route('/add_patient', methods=['POST'])
@login_required
def add_patient():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))
    
    from forms import PatientForm

    form = PatientForm(request.form)
    if form.validate_on_submit():
        patient = Account(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            blood_group=form.blood_group.data,
            user_role="patient"
        )
        patient.set_password(patient.first_name+"123")
        db.session.add(patient)
        db.session.commit()
        return jsonify({"status": "success", "message": f"Patient {patient.first_name} {patient.last_name} added successfully! \n Patient Id:- {patient.user_id}"})
    errors = {field: error[0] for field, error in form.errors.items()}
    return jsonify({"status": "error", "errors": errors})


def view_patient():
    pass

@app.route('/add_prescription', methods=['GET', 'POST'])
@login_required
def add_prescription():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))
    
    from forms import PrescriptionForm

    form = PrescriptionForm()
    if form.validate_on_submit():
        prescription = MedicalReport(
            patient_id=form.patient_id.data,
            doctor_id=current_user.id,
            diagnosis=form.diagnosis.data,
            prescription=form.prescription.data
        )
        db.session.add(prescription)
        db.session.commit()
        flash("Prescription added successfully!", "success")
        return redirect(url_for('doctor_dashboard'))

    return render_template('doctor_dashboard.html', prescription_form=form)

@app.route('/add_xray', methods=['GET', 'POST'])
@login_required
def add_xray():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))
    
    from forms import XRayForm

    form = XRayForm()
    if form.validate_on_submit():
        xray = XRay(
            patient_id=form.patient_id.data,
            image_path=form.image.data.filename
        )
        db.session.add(xray)
        db.session.commit()
        flash("X-Ray details added successfully!", "success")
        return redirect(url_for('doctor_dashboard'))

    return render_template('doctor_dashboard.html', xray_form=form)

@app.route('/search_patient', methods=['GET'])
@login_required
def search_patient():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))

    patient_id = request.args.get('patient_id')
    patient = Account.query.filter_by(user_id=patient_id, user_role="patient").first()
    if patient:
        return render_template('view_patient.html', patient=patient)
    else:
        flash("Patient not found.", "danger")
        return redirect(url_for('doctor_dashboard'))
    
@app.route('/search_disease', methods=['GET'])
@login_required
def search_disease():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))

    disease = request.args.get('disease')
    patients = Account.query.join(MedicalReport).filter(MedicalReport.diagnosis.ilike(f"%{disease}%")).all()
    return render_template('doctor_dashboard.html', patients=patients)

@app.route('/list_patients_by_blood_group', methods=['GET'])
@login_required
def list_patients_by_blood_group():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))

    blood_group = request.args.get('blood_group')
    patients = Account.query.filter_by(blood_group=blood_group, user_role="patient").all()
    return render_template('doctor_dashboard.html', patients=patients)  

if __name__ == '__main__':
    with app.app_context():
        from models import Account, MedicalReport, XRay 
        db.create_all() 
    app.run(debug=True)
