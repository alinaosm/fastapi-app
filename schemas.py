from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Literal

# Company Schemas
class CompanyBase(BaseModel):
    name: str #required
    industry: Optional[str] = None
    url: Optional[HttpUrl] = None
    headcount: Optional[int] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None #optional

class Company(CompanyBase):
    id: int

    class Config:
        from_attributes = True


# JobPosting Schemas
class JobPostingBase(BaseModel):
    title: str
    company_id: int
    compensation_min: Optional[float] = None
    compensation_max: Optional[float] = None
    location_type: Literal["REMOTE", "ONSITE", "HYBRID"]
    employment_type: Optional[Literal["PART_TIME", "FULL_TIME", "CONTRACT"]] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None  
    description: Optional[str] = None

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(JobPostingBase):
    company_id: Optional[int] = None
    title: Optional[str] = None

class JobPosting(JobPostingBase):
    id: int

    class Config:
        from_attributes = True 

class JobDescriptionRequest(BaseModel):
    required_tools: List[str]
    company_culture: Optional[str] = None


# Define LangChain output schema
class JobDescription(BaseModel):
    title: str
    summary: str
    responsibilities: List[str]
    requirements: List[str]
    qualifications: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    tools: List[str]