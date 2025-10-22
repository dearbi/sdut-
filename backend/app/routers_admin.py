from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .db import SessionLocal
from .models import User, Role, Department, UserRole, Patient, Resource, Schedule
from .schemas import UserCreate, UserOut, RoleCreate, DepartmentCreate, PatientCreate, PatientOut, ResourceCreate, ResourceOut, ScheduleCreate, ScheduleOut
from .auth import get_current_user, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Users & Roles & Departments

@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    users = db.query(User).all()
    result = []
    for u in users:
        roles = [r.name for r in u.roles]
        result.append(UserOut(id=u.id, username=u.username, email=u.email, is_active=u.is_active, department_id=u.department_id, roles=roles))
    return result

@router.post("/users", response_model=UserOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    from .auth import get_password_hash
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user_in.password)
    user = User(username=user_in.username, email=user_in.email, hashed_password=hashed, department_id=user_in.department_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, department_id=user.department_id, roles=[])

@router.post("/roles", response_model=str)
def create_role(role_in: RoleCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    if db.query(Role).filter(Role.name == role_in.name).first():
        raise HTTPException(status_code=400, detail="Role exists")
    r = Role(name=role_in.name)
    db.add(r)
    db.commit()
    return r.name

@router.post("/departments", response_model=str)
def create_department(dep_in: DepartmentCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    if db.query(Department).filter(Department.name == dep_in.name).first():
        raise HTTPException(status_code=400, detail="Department exists")
    d = Department(name=dep_in.name)
    db.add(d)
    db.commit()
    return d.name

@router.post("/users/{user_id}/assign-role/{role_name}", response_model=List[str])
def assign_role(user_id: int, role_name: str, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.name == role_name).first()
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or role not found")
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    user = db.query(User).filter(User.id == user_id).first()
    return [r.name for r in user.roles]

# Patients

@router.get("/patients", response_model=List[PatientOut])
def list_patients(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin", "clinician", "staff"]))):
    return db.query(Patient).order_by(Patient.created_at.desc()).all()

@router.post("/patients", response_model=PatientOut)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(["admin", "clinician"]))):
    p = Patient(**patient_in.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(p)
    db.commit()
    return {"ok": True}

# Resources

@router.get("/resources", response_model=List[ResourceOut])
def list_resources(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin", "staff"]))):
    return db.query(Resource).all()

@router.post("/resources", response_model=ResourceOut)
def create_resource(resource_in: ResourceCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    r = Resource(**resource_in.dict())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

# Schedules

@router.get("/schedules", response_model=List[ScheduleOut])
def list_schedules(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin", "staff", "clinician"]))):
    return db.query(Schedule).order_by(Schedule.start_time.desc()).all()

@router.post("/schedules", response_model=ScheduleOut)
def create_schedule(s_in: ScheduleCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(["admin", "staff"]))):
    s = Schedule(**s_in.dict(), created_by=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

# Dashboard metrics

@router.get("/dashboard/metrics")
def dashboard_metrics(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin", "clinician", "staff"]))):
    user_count = db.query(User).count()
    patient_count = db.query(Patient).count()
    resource_count = db.query(Resource).count()
    schedule_count = db.query(Schedule).count()
    # risk distribution
    risk = {}
    for rl, cnt in db.query(Patient.risk_level,).all():
        if rl:
            risk[rl] = risk.get(rl, 0) + 1
    return {
        "users": user_count,
        "patients": patient_count,
        "resources": resource_count,
        "schedules": schedule_count,
        "risk_distribution": risk,
    }