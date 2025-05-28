from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from session import Base
# from datetime import datetime

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

    job_postings = relationship("JobPosting", back_populates="company")

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
    # created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=True)

    company = relationship("Company", back_populates="job_postings") 