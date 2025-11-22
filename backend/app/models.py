from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    department = relationship('Department')
    roles = relationship('Role', secondary='user_roles', backref='users')

class UserRole(Base):
    __tablename__ = 'user_roles'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role_id = Column(Integer, ForeignKey('roles.id'))

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    age = Column(Integer, nullable=True)
    sex = Column(String(10), nullable=True)
    contact = Column(String(100), nullable=True)
    risk_level = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    external_id = Column(String(64), nullable=True, index=True)
    visit_time = Column(DateTime, nullable=True, index=True)
    medical_record_no = Column(String(32), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    type = Column(String(50), nullable=True)  # CT/MRI/血检/床位等
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    status = Column(String(20), default='available')  # available/maintenance/occupied

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id'))
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='scheduled')  # scheduled/cancelled/completed
    created_by = Column(Integer, ForeignKey('users.id'))


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(64), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)