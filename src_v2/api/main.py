"""FastAPI entry point for Design Review Agent."""

from contextlib import asynccontextmanager
import os
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield


app = FastAPI(
    title="Design Review Agent API",
    description="API for uploading PRD documents and prototype images for AI review",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    """Request body for triggering a review."""

    document_path: str
    review_types: list[Literal["prd", "prototype"]]


class ReviewResponse(BaseModel):
    """Response body for review results."""

    report_id: str
    compliance_score: int
    findings: list
    summary: str


class UploadResponse(BaseModel):
    """Response body for file upload."""

    path: str
    type: Literal["prd", "prototype"]
    filename: str


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Upload PRD document or prototype image.

    Automatically detects file type based on extension:
    - Images (.png, .jpg, .jpeg, .gif, .webp) -> prototype
    - Others (.md, .txt, .pdf) -> prd
    """
    ext = os.path.splitext(file.filename)[1].lower()
    is_image = ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return UploadResponse(
        path=file_path,
        type="prototype" if is_image else "prd",
        filename=file.filename,
    )


@app.post("/api/review", response_model=ReviewResponse)
async def trigger_review(req: ReviewRequest) -> ReviewResponse:
    """Trigger a review workflow for uploaded document.

    Args:
        req: ReviewRequest with document_path and review_types

    Returns:
        ReviewResponse with report_id, compliance_score, findings, and summary
    """
    from src_v2.agents.review_agent.workflow import review_graph

    initial_state = {
        "document_path": req.document_path,
        "review_types": req.review_types,
    }

    # Run the review graph
    result = await review_graph.ainvoke(initial_state)

    # Combine findings from both prd and prototype reviews
    all_findings = result.get("prd_findings", []) + result.get("proto_findings", [])

    return ReviewResponse(
        report_id=result.get("report", {}).get("id", "unknown"),
        compliance_score=result.get("compliance_score", 0),
        findings=all_findings,
        summary=result.get("report", {}).get("summary", ""),
    )


@app.get("/api/reports/{report_id}", response_model=ReviewResponse)
async def get_report(report_id: str) -> ReviewResponse:
    """Get a specific report by ID."""
    from src_v2.infrastructure.database.repositories import SQLAlchemyReportRepository

    repo = SQLAlchemyReportRepository()
    report = await repo.find_by_id_async(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReviewResponse(
        report_id=report.id,
        compliance_score=report.compliance_score,
        findings=report.findings,
        summary=report.summary,
    )


@app.get("/api/reports", response_model=list[ReviewResponse])
async def list_reports() -> list[ReviewResponse]:
    """List all reports."""
    from src_v2.infrastructure.database.repositories import SQLAlchemyReportRepository

    repo = SQLAlchemyReportRepository()
    reports = await repo.find_all_async()

    return [
        ReviewResponse(
            report_id=r.id,
            compliance_score=r.compliance_score,
            findings=r.findings,
            summary=r.summary,
        )
        for r in reports
    ]


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
