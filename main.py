from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # allows your API to be accessible from other origins (domains)
from endpoints import companies, jobs
# initialize the app, add CORS, and include routers.

app = FastAPI(title="Job Board API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Board API"} 
