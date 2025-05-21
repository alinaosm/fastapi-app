from fastapi import FastAPI, Query, Path, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from sqlalchemy import create_engine, Column, Integer, String, Float, text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
import enum
from datetime import datetime

# SQLAlchemy setup 
DATABASE_URL = "postgresql://postgres:password@db.abc.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


app = FastAPI()

# This is our Pydantic data model - what an application looks like
class Candidate(BaseModel):
    candidate_id: str 
    name: str 
    email: str 
    job_id: str | None = None

# data model to add a new company to the Company table
class CompanyAdd(BaseModel):
    name: str
    industry: str
    url: str
    headcount: int
    country: str
    state: str
    city: str

# SQLAlchemy model for the Company table
class Company(Base):
    __tablename__ = "Company"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    url = Column(String, nullable=True)
    headcount = Column(Integer, nullable=False)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)

class LocationTypeEnum(str, enum.Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"

class EmploymentTypeEnum(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"

class JobPosting(Base):
    __tablename__ = "JobPosting"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("Company.id"), nullable=False)
    compensation_min = Column(Float, nullable=True)
    compensation_max = Column(Float, nullable=True)
    location_type = Column(Enum(LocationTypeEnum), nullable=False)
    employment_type = Column(Enum(EmploymentTypeEnum), nullable=True)
    is_active = Column(Boolean, nullable=True)
    created_at = Column(String, nullable=True)

    company = relationship("Company") 

class JobPostingCreate(BaseModel):
    title: str
    company_id: int
    compensation_min: Optional[float] = None  # Optional allows None (null)
    compensation_max: Optional[float] = None
    location_type: Literal["REMOTE", "ONSITE", "HYBRID"]
    employment_type: Optional[Literal["PART_TIME", "FULL_TIME", "CONTRACT"]] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None  # or datetime if you want to parse dates

    class Config:
        orm_mode = True  # Make Pydantic model compatible with SQLAlchemy ORM

# This is our "database" - just a list in memory - cache memory
applications: List[Candidate] = []

#creating a db connection session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    
    

@app.get("/jobs")
def get_all_job_postings(db: Session = Depends(get_db)):
    result = db.execute(text('SELECT * FROM "JobPosting"'))
    rows = result.fetchall()
    #format each row as a String
    output = []
    for row in rows:
        output.append(str(dict(row._mapping)))
    return output   

@app.post("/jobs")
def create_job_posting(job: JobPostingCreate, db: Session = Depends(get_db)):
    new_job = JobPosting(**job.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@app.put("/jobs/{job_id}")
def update_job(job_id: int, job: JobPostingCreate, db: Session = Depends(get_db)):
    job_to_update = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if job_to_update:
        job_to_update.title = job.title
        job_to_update.company_id = job.company_id
        job_to_update.compensation_min = job.compensation_min
        job_to_update.compensation_max = job.compensation_max
        job_to_update.location_type = job.location_type
        job_to_update.employment_type = job.employment_type
        job_to_update.is_active = job.is_active
        job_to_update.created_at = job.created_at   
        db.commit()
        db.refresh(job_to_update)
        return job_to_update
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if job:
        db.delete(job)
        db.commit()
    return {"message": f"Job {job_id}deleted successfully"}

@app.post("/companies")
def add_company(company: CompanyAdd, db: Session = Depends(get_db)):
    new_company = Company(**company.model_dump())
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

@app.get("/companies")
def get_all_companies(db: Session = Depends(get_db)):
    result = db.execute(text('SELECT * FROM "Company"'))
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]

@app.put("/companies/{company_id}")
def update_company(company_id: int, company: CompanyAdd, db: Session = Depends(get_db)):
    company_to_update = db.query(Company).filter(Company.id == company_id).first()
    if company_to_update:
        company_to_update.name = company.name
        company_to_update.industry = company.industry   
        company_to_update.url = company.url
        company_to_update.headcount = company.headcount
        company_to_update.country = company.country
        company_to_update.state = company.state
        company_to_update.city = company.city
        db.commit()
        db.refresh(company_to_update)   
        return company_to_update
    else:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

@app.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company:
        db.delete(company)
        db.commit()
    return {"message": f"Company {company_id} deleted successfully"}
