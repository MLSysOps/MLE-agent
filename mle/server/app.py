import os
import json
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from mle.workflow import report
from mle.utils import check_config

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReportRequest(BaseModel):
    """
    ReportRequest: the request body for generating a report
    """
    repo: str
    username: str
    token: Optional[str] = None
    okr: Optional[str] = None


@app.get("/")
def root():
    """
    read_root: read the root.
    :return: the root.
    """
    return {"Welcome to": "MLE-Agent!"}


@app.get("/latest_report", response_class=JSONResponse)
def read_latest_report():
    """
    read_latest_report: read the latest progress report.
    :return: the content of the latest progress report as plain text.
    """
    if not check_config():
        raise HTTPException(
            status_code=400,
            detail="`project.yml` not found. Please start the MLE server under an MLE-Agent project directory."
        )

    reports_dir = os.getcwd()
    report_files = [f for f in os.listdir(reports_dir) if f.startswith("progress_report_") and f.endswith(".json")]

    if not report_files:
        raise HTTPException(status_code=404, detail="No progress reports found.")

    latest_report = max(report_files, key=lambda f: datetime.strptime(f, "progress_report_%Y_%m_%d.json"))
    try:
        with open(os.path.join(reports_dir, latest_report), 'r') as file:
            report_dict = json.load(file)
            report_dict.update({"file": latest_report})
            return JSONResponse(content=report_dict)
    except IOError:
        raise HTTPException(status_code=500, detail="Error reading the latest report file.")


@app.post("/gen_report")
def gen_report(report_request: ReportRequest):
    """
    Generate a report synchronously based on the provided GitHub repository and username.
    Optionally includes OKR text.

    Example payload:

    curl -X POST http://localhost:8000/gen_report \
     -H "Content-Type: application/json" \
     -d '{
           "token": "***",
           "repo": "MLSysOps/MLE-agent",
           "username": "huangyz0918",
           "okr": "Improve system efficiency by 20% this quarter"
         }'
    """
    try:
        # Run report generation synchronously
        result = report(
            os.getcwd(),
            report_request.repo,
            report_request.username,
            report_request.token,
            okr_str=report_request.okr,
            model="gpt-4o",
        )

        return {
            "message": "Report generation completed",
            "repo": report_request.repo,
            "username": report_request.username,
            "okr_provided": report_request.okr is not None,
            "result": result  # Assuming the report function returns some result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in report generation process: {e}")


@app.post("/gen_report_async")
async def gen_report_async(report_request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate a report (async) based on the provided GitHub repository and username.
    Optionally includes OKR text.

    Example payload:

    curl -X POST http://localhost:8000/gen_report_async \
     -H "Content-Type: application/json" \
     -d '{
           "token": "***",
           "repo": "MLSysOps/MLE-agent",
           "username": "huangyz0918",
           "okr": "Improve system efficiency by 20% this quarter"
         }'
    """
    try:
        # Trigger report generation in the background
        background_tasks.add_task(
            report,
            os.getcwd(),
            report_request.repo,
            report_request.username,
            report_request.token,
            okr_str=report_request.okr,
            model="gpt-4o",
        )

        return {
            "message": "Report generation started",
            "repo": report_request.repo,
            "username": report_request.username,
            "okr_provided": report_request.okr is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in report generation process: {e}")
