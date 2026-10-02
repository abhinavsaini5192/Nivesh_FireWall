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
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.schemas.input import ContentInput, ChannelType
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from pydantic import BaseModel

class ActionAnalysisPayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None

class SourceAnalysisPayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None
    actions: Optional[ActionAnalysis] = None

class EvidenceVerificationPayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None
    sources: Optional[SourceAnalysis] = None

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
actions_engine = ActionIntelligenceEngine()
sources_engine = SourceIntelligenceEngine()
evidence_engine = EvidenceVerificationEngine()


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
            "Engine 3: Action Intelligence Engine",
            "Engine 4: Source Intelligence Engine",
            "Engine 5: Evidence Verification Engine",
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


@app.post(
    "/api/v1/actions/analyze",
    response_model=ActionAnalysis,
    tags=["Action Intelligence (Engine 3)"],
    summary="Extract atomic canonical actions from NormalizedContent and ClaimAnalysis"
)
async def analyze_actions(request: Request):
    """Consumes NormalizedContent and optional ClaimAnalysis, producing structured ActionAnalysis."""
    try:
        body = await request.json()
        if "content" in body:
            payload = ActionAnalysisPayload(**body)
            content = payload.content
            claims = payload.claims
        else:
            # Direct NormalizedContent payload
            content = NormalizedContent(**body)
            claims = None

        # If claims not provided, automatically generate via Engine 2
        if claims is None:
            claims = claims_engine.analyze(content)

        return actions_engine.analyze(content, claims)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Action analysis failed: {str(e)}"
        )


@app.post(
    "/api/v1/sources/analyze",
    response_model=SourceAnalysis,
    tags=["Source Intelligence (Engine 4)"],
    summary="Discover, route, and retrieve authoritative source documents and evidence candidates"
)
async def analyze_sources(request: Request):
    """Consumes NormalizedContent, ClaimAnalysis, and optional ActionAnalysis to retrieve source evidence."""
    try:
        body = await request.json()
        if "content" in body:
            payload = SourceAnalysisPayload(**body)
            content = payload.content
            claims = payload.claims
            actions = payload.actions
        else:
            # Direct NormalizedContent payload
            content = NormalizedContent(**body)
            claims = None
            actions = None

        # Auto-pipeline fallbacks if upstream analyses not supplied
        if claims is None:
            claims = claims_engine.analyze(content)
        if actions is None:
            actions = actions_engine.analyze(content, claims)

        return sources_engine.discover_and_retrieve(content, claims, actions)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Source analysis failed: {str(e)}"
        )


@app.post(
    "/api/v1/evidence/verify",
    response_model=EvidenceAnalysis,
    tags=["Evidence Verification (Engine 5)"],
    summary="Evaluate retrieved source material against canonical claims"
)
async def verify_evidence(request: Request):
    """Consumes NormalizedContent, ClaimAnalysis, and SourceAnalysis to evaluate claim truth/falsity."""
    try:
        body = await request.json()
        if "content" in body:
            payload = EvidenceVerificationPayload(**body)
            content = payload.content
            claims = payload.claims
            sources = payload.sources
        else:
            # Direct NormalizedContent payload
            content = NormalizedContent(**body)
            claims = None
            sources = None

        # Auto-pipeline fallbacks if upstream analyses not supplied
        if claims is None:
            claims = claims_engine.analyze(content)
        if sources is None:
            actions = actions_engine.analyze(content, claims)
            sources = sources_engine.discover_and_retrieve(content, claims, actions)

        return evidence_engine.verify(content, claims, sources)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Evidence verification failed: {str(e)}"
        )



