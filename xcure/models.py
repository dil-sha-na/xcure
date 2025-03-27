from extensions import db
from sqlalchemy import event
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class Account(UserMixin, db.Model):
    __tablename__ = 'account'
    
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
    
    received_documents = db.relationship(
        'Document',
        foreign_keys='Document.patient_id',
        back_populates='patient',
        lazy=True
    )
    
    uploaded_documents = db.relationship(
        'Document',
        foreign_keys='Document.doctor_id',
        back_populates='doctor',
        lazy=True
    )

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

class Document(db.Model):
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_by = db.Column(db.String(200), nullable=False)
    upload_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    patient = db.relationship(
        'Account',
        foreign_keys=[patient_id],
        back_populates='received_documents'
    )

    doctor = db.relationship(
        'Account',
        foreign_keys=[doctor_id],
        back_populates='uploaded_documents'
    )



class Prescription(db.Model):
    __tablename__ = "prescription"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    prescription = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    patient = db.relationship(
        "Account", foreign_keys=[patient_id], backref="prescriptions"
    )
    doctor = db.relationship(
        "Account", foreign_keys=[doctor_id], backref="prescriptions_written"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": f"{self.patient.first_name} {self.patient.last_name}",
            "doctor_id": self.doctor_id,
            "doctor_name": f"{self.doctor.first_name} {self.doctor.last_name}",
            "prescription": self.prescription,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self):
        return f"<Prescription {self.id}, Patient: {self.patient_id}, Doctor: {self.doctor_id}>"
