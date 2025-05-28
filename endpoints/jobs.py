from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from session import get_db
import models
import schemas
from openai import OpenAI
import json


client = OpenAI()
router = APIRouter()

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


# dictionary defines a function schema / OpenAI tool schema that is passed to the OpenAI API, 
# for structured job description, instructing the model how to structure the response.
# telling GPT Instead of writing free-form text, return the job description using this structured JSON format.
job_description_function = {
    "type": "function", # Instructs the model that this is a tool of type 'function'
    "function": {
        "name": "generate_structured_job_description", # The name of the function to be called
        "description": "Generate a structured job description for an AI job",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the job"
                },
                "summary": {
                    "type": "string",
                    "description": "A brief summary of the role"
                },
                "responsibilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of key responsibilities"
                },
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of key requirements or qualifications"
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tools or technologies required for the role"
                }
            },
            "required": ["title", "summary", "responsibilities", "requirements", "tools"]
        }
    }
}

@router.post("/{job_id}/description", response_model=dict)
def gen_job_description(job_id: int, payload: schemas.JobDescriptionRequest, db: Session = Depends(get_db)):
    job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    company = db.query(models.Company).filter(models.Company.id == job.company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

# Pass user + job + company info in a natural prompt format.
    prompt = f"""
    Generate a structured job description for the following AI role:
    Job Title: {job.title}
    Company: {company.name}
    Industry: {company.industry}
    Location: {job.location_type}
    Employment Type: {job.employment_type}
    Required Tools: {', '.join(payload.required_tools)}
    """

# send a chat-based prompt to an OpenAI model and receive a generated response
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior technical recruiter."},
            {"role": "user", "content": prompt}
        ],
        tools=[job_description_function], # tools parameter sends the schema.
        tool_choice={"type": "function", "function": {"name": "generate_structured_job_description"}}
    )

    tool_call = response.choices[0].message.tool_calls[0]
    structured_description = json.loads(tool_call.function.arguments)
    #tool_call.function.arguments is a JSON string that contains the structured job description.
    #json.loads() converts the JSON string into a Python dictionary.

# store the full structured result into the description column of the JobPosting table.
    job.description = (
        structured_description["summary"] + "\n\n" +
        "Responsibilities:\n" + "\n".join(structured_description["responsibilities"]) + "\n\n" +
        "Requirements:\n" + "\n".join(structured_description["requirements"]) + "\n\n" +
        "Tools:\n" + "\n".join(structured_description["tools"])
    )
    db.commit()
    db.refresh(job)

#Sends the structured description back to the client (Postman, frontend, etc).
    return {"job_id": job_id, "structured_description": structured_description}




# Save only the summary into the description column of the JobPosting table.
#    job.description = structured_description["summary"]
# save summary and responsibilities into the description column of the JobPosting table.
# summary = structured_description["summary"]
# responsibilities = structured_description["responsibilities"]
# job.description = summary + "\n\nResponsibilities:\n" + "\n".join(f"- {item}" for item in responsibilities)



