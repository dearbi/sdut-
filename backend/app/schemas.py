from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    department_id: Optional[int] = None
    roles: List[str] = []

    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str

class DepartmentCreate(BaseModel):
    name: str

# Patient
class PatientCreate(BaseModel):
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    contact: Optional[str] = None
    risk_level: Optional[str] = None
    notes: Optional[str] = None
    external_id: Optional[str] = None
    visit_time: Optional[datetime] = None

class PatientOut(BaseModel):
    id: int
    name: str
    age: Optional[int]
    sex: Optional[str]
    contact: Optional[str]
    risk_level: Optional[str]
    notes: Optional[str]
    external_id: Optional[str]
    visit_time: Optional[datetime]
    medical_record_no: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientSyncRequest(BaseModel):
    name: str
    external_id: Optional[str] = None
    visit_time: Optional[datetime] = None
    risk_level: Optional[str] = None
    notes: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    contact: Optional[str] = None

# Resource
class ResourceCreate(BaseModel):
    name: str
    type: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = "available"

class ResourceOut(BaseModel):
    id: int
    name: str
    type: Optional[str]
    department_id: Optional[int]
    status: str

    class Config:
        from_attributes = True

# Schedule
class ScheduleCreate(BaseModel):
    resource_id: int
    patient_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    status: Optional[str] = "scheduled"

class ScheduleOut(BaseModel):
    id: int
    resource_id: int
    patient_id: Optional[int]
    start_time: datetime
    end_time: datetime
    status: str
    created_by: int

    class Config:
        from_attributes = True