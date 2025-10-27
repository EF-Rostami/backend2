from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import Base, engine
from config import ALLOWED_ORIGINS


# Import all routers
from routers import (
    auth, admission, students, teachers, 
    classes, courses, exams, grades,
    attendance, fees, registrations, 
    parents, dashboard, absence_excuses, appointment, events
)

app = FastAPI(title="Elementary School Management System")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

# Include all routers
app.include_router(auth.router)
app.include_router(admission.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(classes.router)
app.include_router(courses.router)
app.include_router(exams.router)
app.include_router(grades.router)
app.include_router(attendance.router)
app.include_router(fees.router)
app.include_router(registrations.router)
app.include_router(parents.router)
app.include_router(dashboard.router)
app.include_router(absence_excuses.router)
app.include_router(appointment.router)
app.include_router(events.router)

@app.get("/")
async def root():
    return {
        "message": "Elementary School Management System API", 
        "version": "2.0",
        "status": "All systems operational"
    }

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    return JSONResponse(content={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)