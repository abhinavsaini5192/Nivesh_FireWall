"""FastAPI Application exposing Content Intelligence Engine API.

Provides:
- POST /api/v1/content/analyze (JSON or multipart file upload)
- GET  /api/v1/health
"""

from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nivesh.engine import ContentIntelligenceEngine, ENGINE_VERSION
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.schemas.input import ContentInput, ChannelType
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis

# Initialize FastAPI application
app = FastAPI(
    title="Nivesh Firewall — Backend API",
    description="Multi-engine security API for financial content and claim intelligence.",
    version=ENGINE_VERSION,
)

# Enable CORS for browser integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate singleton engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()


@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """Health status check."""
    return {
        "status": "healthy",
        "engine": "Content Intelligence Engine",
        "engines": [
            "Engine 1: Content Intelligence Engine",
            "Engine 2: Claim Intelligence Engine",
        ],
        "version": ENGINE_VERSION,
    }


@app.post(
    "/api/v1/content/analyze",
    response_model=NormalizedContent,
    tags=["Content Intelligence (Engine 1)"],
    summary="Analyze and normalize content from text, URL, or image"
)
async def analyze_content(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Optional image file upload"),
    text: Optional[str] = Form(None, description="Raw text (form-data)"),
    url: Optional[str] = Form(None, description="Target URL (form-data)"),
    channel: Optional[ChannelType] = Form("unknown", description="Source channel (form-data)"),
):
    """Unified analysis endpoint supporting both JSON and multipart/form-data."""
    try:
        content_type = request.headers.get("content-type", "")

        # 1. JSON Request Body
        if "application/json" in content_type:
            body = await request.json()
            input_model = ContentInput(**body)
            return content_engine.process(input_model)

        # 2. Multipart/Form-data Upload
        image_bytes: Optional[bytes] = None
        if file is not None:
            image_bytes = await file.read()

        input_model = ContentInput(
            text=text,
            url=url,
            image_bytes=image_bytes,
            channel=channel or "unknown",
        )
        return content_engine.process(input_model)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Content analysis failed: {str(e)}"
        )


@app.post(
    "/api/v1/claims/analyze",
    response_model=ClaimAnalysis,
    tags=["Claim Intelligence (Engine 2)"],
    summary="Extract atomic canonical claims from NormalizedContent"
)
async def analyze_claims(content: NormalizedContent):
    """Consumes NormalizedContent and produces atomic, canonical ClaimAnalysis."""
    try:
        return claims_engine.analyze(content)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Claim analysis failed: {str(e)}"
        )

