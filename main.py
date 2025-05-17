from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Application(BaseModel):
    candidate_id: str
    name: str
    email: str
    job_id: str

class ApplicationUpdate(BaseModel):
    candidate_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    job_id: Optional[str] = None


applications = []

@app.post("/applications")
def submit_application(application: Application):
    applications.append(application)
    return {
        "status": "success", 
        "message": f"Application submitted for {application.name}"
        }

@app.get("/applications")
def get_applications(company_name: Optional[str] = None, candidate_email: Optional[str] = None):
    if company_name and candidate_email:
        return f"Here is your application for {company_name} and your email is {candidate_email}"
    elif company_name:
        return f"Here is your application for {company_name}"
    elif candidate_email:
        return f"Here is your application for {candidate_email}"
    else:
        return f"Here are all of your applications: {applications}"

@app.get("/applications/{candidate_id}")
def get_application_by_id(candidate_id: str):
    for application in applications:
        if application.candidate_id == candidate_id:
            return application
    raise HTTPException(status_code=404, detail="Application not found")

@app.put("/applications/{candidate_id}")
def update_application(candidate_id: str, updated_application: Application):
    for i, app in enumerate(applications):
        if app.candidate_id == candidate_id:
            applications[i] = updated_application
            return {
                "status": "success", 
                "message": f"Application for {updated_application.candidate_id} updated successfully",
                "data": updated_application
                }
    raise HTTPException(status_code=404, detail="Application not found")    

@app.patch("/applications/{candidate_id}")
def patch_application(candidate_id: str, application_update: ApplicationUpdate):
    for i, app in enumerate(applications):
        if app.candidate_id == candidate_id:
            updated_data = app.dict()
            update_fields = application_update.dict(exclude_unset=True)
            updated_data.update(update_fields)
            applications[i] = Application(**updated_data)
            return {
                "status": "success",
                "message": "Application updated successfully",
                "data": applications[i]
            }
    raise HTTPException(status_code=404, detail="Application not found")


@app.delete("/applications/{candidate_id}")
def delete_application(candidate_id: str):
    for i, app in enumerate(applications):
        if app.candidate_id == candidate_id:
            applications.pop(i)
            return {"status": "success", "message": "Application deleted successfully"}
    raise HTTPException(status_code=404, detail="Application not found")         