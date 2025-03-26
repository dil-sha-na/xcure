from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from extensions import db, bcrypt, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os, time


# Configure upload folder
UPLOAD_FOLDER = 'patient_documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'png', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'excure2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.template_filter('format_datetime')
def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    if isinstance(value, str):
        value = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")
    return value.strftime(format)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_page'  

from flask_migrate import Migrate

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return Account.query.get(int(user_id)) if user_id else None 

@app.route('/')
def index():
    user= load_user(session.get('_user_id'))
    if user:
        if user.user_role == "doctor":
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
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
                flash(f"Doctor Registration Successful. Doctor ID: {doctor.user_id}", "message")
                return redirect(url_for('login_page'))
            except IntegrityError:
                db.session.rollback() 
                flash("An error occurred. Please try again.", "error")
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
                    flash("Doctor login successful!", "message")
                    return redirect(url_for('doctor_dashboard'))
                else:
                    flash("Invalid Doctor ID or password", "error")

        else: 
            if patient_form.validate_on_submit():
                patient_id = patient_form.patient_id.data

                patient = Account.query.filter_by(user_id=patient_id, user_role="patient").first()
                if patient:
                    login_user(patient)  
                    flash("Patient login successful!", "message")
                    return redirect(url_for('patient_dashboard'))
                else:
                    flash("Invalid Patient ID", "error")
    return render_template("login.html", doctor_form=doctor_form, patient_form=patient_form)

@app.route('/download-document/<int:doc_id>')
@login_required
def download_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    
    return send_from_directory(
        os.path.dirname(document.file_path),
        os.path.basename(document.file_path),
        as_attachment=True,
        download_name=f"{document.name}{os.path.splitext(document.file_path)[1]}"
    )

@app.route('/delete-document/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    
    try:
        # Remove file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete record from database
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(request.referrer)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    patient_id = request.args.get('patient_id')
    
    if patient_id:
        patient = Account.query.options(
            db.joinedload(Account.received_documents).joinedload(Document.doctor)
        ).filter_by(user_id=patient_id, user_role="patient").first()
        
        return render_template(
            'doctor_dashboard.html', 
            active_section="patient-search",
            patient=patient,
            has_patient=bool(patient),
            searched_id=patient_id
        )
    
    return render_template(
        'doctor_dashboard.html', 
        active_section="patient-search"
    )
@app.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    if 'document' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.referrer)
    
    file = request.files['document']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer)
    
    if not allowed_file(file.filename):
        flash('File type not allowed', 'error')
        return redirect(request.referrer)
    
    patient_id = request.form.get('patient_id')
    document_name = request.form.get('document_name')
    
    if not patient_id or not document_name:
        flash('Missing required fields', 'error')
        return redirect(request.referrer)
    
    patient = Account.query.filter_by(id=patient_id, user_role='patient').first()
    if not patient:
        flash('Patient not found', 'error')
        return redirect(request.referrer)
    
    filename = secure_filename(file.filename)
    unique_filename = f"{patient.user_id}_{int(time.time())}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        new_doc = Document(
            name=document_name,
            file_path=file_path,
            upload_by=current_user.user_id,
            patient_id=patient.id,
            doctor_id=current_user.id
        )
        db.session.add(new_doc)
        db.session.commit()
        
        flash('Document uploaded successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading document: {str(e)}', 'error')
    
    return redirect(request.referrer)



@app.route('/doctor/patients')
def patients_by_bg():
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    selected_bg = request.args.get("bg")
    
    if selected_bg:
        patients = Account.query.filter(
            Account.user_role == "patient",
            Account.blood_group == selected_bg
        ).all()
    else:
        patients = Account.query.filter_by(user_role="patient").all()
    
    return render_template(
        'patients_by_bg.html', 
        active_section="patients-by-bg",
        patients=patients,
        blood_groups=blood_groups,
        selected_bg=selected_bg
    )

@app.route('/doctor/add_patient', methods=['GET','POST'])
@login_required
def add_patient():
    from forms import PatientForm
    form = PatientForm()
    if request.method == "POST":
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
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return jsonify({"status": "error", "errors": errors})
    else:   
        return render_template('add_patient.html',patient_form=form,active_section="add-patient")
   

@app.route('/search_patient', methods=['GET'])
@login_required
def search_patient():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))

    patient_id = request.args.get('patient_id')
    patient = Account.query.filter_by(user_id=patient_id, user_role="patient").first()
    if patient:
        return jsonify({
            "status": "success",
            "patient": {
                "patient_id": patient.user_id,
                "full_name": patient.first_name + " "  + patient.last_name,
                "email": patient.email,
                "phone_number": patient.phone_number,
                "blood_group": patient.blood_group,
                "date_of_birth": patient.date_of_birth,
                "account_created_at": patient.created_at
                }})
    else:
        return jsonify({"status": "error", "message": "Patient not found!"})


@app.route('/list_patients_by_blood_group', methods=['GET'])
@login_required
def list_patients_by_blood_group():
    if current_user.user_role != "doctor":
        flash("Access denied. You are not a doctor.", "danger")
        return redirect(url_for('login_page'))

    blood_group = request.args.get('blood_group')
    patients = Account.query.filter_by(blood_group=blood_group, user_role="patient").all()
    return render_template('doctor_dashboard.html', patients=patients)  

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        from models import Account, Document 
        db.create_all() 
    app.run(debug=True)
