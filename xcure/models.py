from extensions import db
from sqlalchemy import event
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(200), nullable=True)
    last_name = db.Column(db.String(200), nullable=True)
    email= db.Column(db.String(200), nullable=False)
    password= db.Column(db.String(200), nullable=True)
    date_of_birth = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    user_id = db.Column(db.String(200), nullable=False, unique=True)
    user_role = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("MedicalReport", back_populates="patient", foreign_keys="MedicalReport.patient_id", lazy=True)
    created_reports = relationship("MedicalReport", back_populates="created_by", foreign_keys="MedicalReport.doctor_id", lazy=True)

    def __repr__(self):
        return f"<Account {self.first_name}>"
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
def generate_user_id(mapper, connection, target):
    role_prefix = "DOC" if target.user_role.lower() == "doctor" else "PAT"

    with db.session.begin_nested():  
        last_user = db.session.query(Account).filter(Account.user_id.like(f"{role_prefix}%")).order_by(Account.id.desc()).first()

        if last_user and last_user.user_id:
            last_number = int(last_user.user_id[len(role_prefix):]) 
            new_number = last_number + 1
        else:
            new_number = 1 

        new_user_id = f"{role_prefix}{new_number:04d}"
        target.user_id = new_user_id

event.listen(Account, 'before_insert', generate_user_id)

class MedicalReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Explicitly specify foreign_keys in relationships
    patient = relationship("Account", foreign_keys=[patient_id], back_populates="reports")
    created_by = relationship("Account", foreign_keys=[doctor_id], back_populates="created_reports")
    xrays = relationship("XRay", back_populates="report")


class XRay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('medical_report.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    report = relationship("MedicalReport", back_populates="xrays")

    def __repr__(self):
        return f"<XRay for Report {self.report_id}>"

