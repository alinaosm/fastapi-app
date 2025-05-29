from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from session import get_db
import models
import schemas
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model


router = APIRouter() # group related endpoints

@router.post("/", response_model=schemas.JobPosting)
def create_job_posting(job: schemas.JobPostingCreate, db: Session = Depends(get_db)):
    # Verify company exists
    company = db.query(models.Company).filter(models.Company.id == job.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_job = models.JobPosting(**job.model_dump()) #create a JobPosting Object with default values (**job.model_dump()) just pass all the required constructor values
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/", response_model=List[schemas.JobPosting])
def read_job_postings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = db.query(models.JobPosting).offset(skip).limit(limit).all()
    return jobs

#jobs/6
@router.get("/{job_id}", response_model=schemas.JobPosting)
def read_job_posting(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return db_job

@router.put("/{job_id}", response_model=schemas.JobPosting)
def update_job_posting(job_id: int, job: schemas.JobPostingUpdate, db: Session = Depends(get_db)):
    db_job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    # If company_id is being updated, verify the new company exists
    if job.company_id is not None:
        company = db.query(models.Company).filter(models.Company.id == job.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = job.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/{job_id}")
def delete_job_posting(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job posting deleted successfully"} 


# endpoint to generate a structured job description using LangChain

# input prompt that will be sent to the LLM. "user" message uses {placeholders} to dynamically insert job-related fields.
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a senior technical recruiter."),
    ("user", """Generate a structured job description for the following AI role:

Job Title: {job_title}
Company: {company_name}
Industry: {industry}
Location: {location}
Employment Type: {employment_type}
Required Tools: {required_tools}

Please include the following sections in your response:
- Title
- Summary
- Responsibilities
- Requirements
- Qualifications
- Benefits
- Tools""")
])


# initialize a gpt-4o-mini model from OpenAI
model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    temperature=0,
    model_kwargs={
        "max_tokens": 500,
        "logprobs": True,
        "top_logprobs": 4
    }
).with_structured_output(schemas.JobDescription) # tells LangChain to parse the model's response into a Pydantic model (JobDescription), ensuring consistency.

chain = prompt_template | model # Combine Prompt and Model. Accepts prompt variables as input. Feeds them into the model.

@router.post("/{job_id}/description", response_model=dict)
def gen_job_description(job_id: int, payload: schemas.JobDescriptionRequest, db: Session = Depends(get_db)):
    job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")

    company = db.query(models.Company).filter(models.Company.id == job.company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")


    structured_description = chain.invoke({ # Use LangChain to generate a structured job description. Calls the LLM with dynamic prompt variables.
        "job_title": job.title,
        "company_name": company.name,
        "industry": company.industry,
        "location": job.location_type,
        "employment_type": job.employment_type,
        "required_tools": ", ".join(payload.required_tools)
    })
# The result is parsed into a JobDescription Pydantic object because of .with_structured_output(schemas.JobDescription)
# Combine structured fields into a human-readable job description string.
    job.description = (
        "Title:\n" + structured_description.title + "\n\n" +
        "Summary:\n" + structured_description.summary + "\n\n" +
        "Responsibilities:\n" + "\n".join(structured_description.responsibilities) + "\n\n" +
        "Requirements:\n" + "\n".join(structured_description.requirements) + "\n\n" +
        "Qualifications:\n" + "\n".join(structured_description.qualifications) + "\n\n" +
        "Benefits:\n" + "\n".join(structured_description.benefits) + "\n\n" +
        "Tools:\n" + "\n".join(structured_description.tools)
    )

    db.commit()
    db.refresh(job)

    return {"job_id": job_id, "structured_description": structured_description.model_dump()}

# model_dump() is the Pydantic v2 method to serialize a model to a dictionary.


# return the formatted string like the one saved to the database.
# return {"job_id": job_id, "description": job.description}


# Save only the summary into the description column of the JobPosting table.
#    job.description = structured_description["summary"]
# save summary and responsibilities into the description column of the JobPosting table.
# summary = structured_description["summary"]
# responsibilities = structured_description["responsibilities"]
# job.description = summary + "\n\nResponsibilities:\n" + "\n".join(f"- {item}" for item in responsibilities)



