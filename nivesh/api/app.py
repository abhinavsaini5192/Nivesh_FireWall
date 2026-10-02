"""FastAPI Application exposing Content Intelligence Engine API.

Provides:
- POST /api/v1/content/analyze (JSON or multipart file upload)
- GET  /api/v1/health
"""

from typing import Optional
from urllib.parse import urlparse
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nivesh.engine import ContentIntelligenceEngine, ENGINE_VERSION
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecision, PolicyContext
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityAnalysis, ClaimedEntity
from nivesh.behaviour.engine import BehaviouralSignalEngine
from nivesh.behaviour.schemas import BehaviouralAnalysis
from nivesh.orchestrator.service import (
    ProductOrchestrator,
    format_firewall_response,
    sanitize_sensitive_data,
)
from nivesh.schemas.firewall import (
    FirewallAnalyzeRequest,
    FirewallAnalysisResponse,
    FirewallApiError,
)
from nivesh.behaviour.event_model import InteractionEvent, InteractionHistory
from nivesh.schemas.input import ContentInput, ChannelType
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
    FingerprintMatch,
    FingerprintAnalysis,
)
from pydantic import BaseModel
from datetime import datetime, timezone

class BehaviouralAnalyzePayload(BaseModel):
    content: Optional[NormalizedContent] = None
    text: Optional[str] = None
    claims: Optional[ClaimAnalysis] = None
    actions: Optional[ActionAnalysis] = None
    threat: Optional[ThreatAnalysis] = None
    fingerprint: Optional[FingerprintAnalysis] = None
    identity: Optional[IdentityAnalysis] = None
    interaction_history: Optional[InteractionHistory] = None

class BehaviouralEventPayload(BaseModel):
    session_id: str
    event: InteractionEvent

class IdentityVerificationPayload(BaseModel):
    content: Optional[NormalizedContent] = None
    text: Optional[str] = None
    claims: Optional[ClaimAnalysis] = None
    sources: Optional[SourceAnalysis] = None
    evidence: Optional[EvidenceAnalysis] = None
    threat: Optional[ThreatAnalysis] = None

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

class ThreatAnalysisPayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None
    actions: Optional[ActionAnalysis] = None
    sources: Optional[SourceAnalysis] = None
    evidence: Optional[EvidenceAnalysis] = None

class FingerprintMatchPayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None
    actions: Optional[ActionAnalysis] = None
    sources: Optional[SourceAnalysis] = None
    evidence: Optional[EvidenceAnalysis] = None
    threat: Optional[ThreatAnalysis] = None

class FingerprintDisputePayload(BaseModel):
    reason: str
    actor: Optional[str] = "user"

class PolicyDecidePayload(BaseModel):
    content: NormalizedContent
    claims: Optional[ClaimAnalysis] = None
    actions: Optional[ActionAnalysis] = None
    sources: Optional[SourceAnalysis] = None
    evidence: Optional[EvidenceAnalysis] = None
    threat: Optional[ThreatAnalysis] = None
    fingerprint: Optional[FingerprintAnalysis] = None
    identity: Optional[IdentityAnalysis] = None
    behaviour: Optional[BehaviouralAnalysis] = None
    context: Optional[PolicyContext] = None


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


@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "Content Intelligence Engine",
        "version": ENGINE_VERSION,
        "engines": [
            "Engine 1: Content Intelligence Engine",
            "Engine 2: Claim Intelligence Engine",
            "Engine 3: Action Intelligence Engine",
            "Engine 4: Source Intelligence Engine",
            "Engine 5: Evidence Verification Engine",
            "Engine 6: Threat & Attack-Path Intelligence Engine",
            "Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine",
            "Engine 8: Policy & Intervention Engine",
            "Engine 9: Identity Verification & Entity Resolution Engine",
            "Engine 10: Behavioural Signal Intelligence Engine",
        ],
        "firewall": "Nivesh Firewall Phase 11.4",
    }


@app.exception_handler(RequestValidationError)
async def firewall_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Cleanly formats validation errors for the unified firewall API."""
    if request.url.path.startswith("/api/v1/firewall"):
        return JSONResponse(
            status_code=400,
            content=FirewallApiError(
                error_code="INVALID_REQUEST",
                message="Malformed request payload or validation failure.",
                details={"errors": [e.get("msg", str(e)) for e in exc.errors()]},
            ).model_dump(),
        )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Instantiate singleton engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()
actions_engine = ActionIntelligenceEngine()
sources_engine = SourceIntelligenceEngine()
evidence_engine = EvidenceVerificationEngine()
threat_engine = ThreatIntelligenceEngine()
fingerprint_engine = ScamFingerprintEngine()
policy_engine = PolicyInterventionEngine()
identity_engine = IdentityVerificationEngine()
behaviour_engine = BehaviouralSignalEngine()

# Canonical Product Orchestrator singleton wiring all 10 engines
firewall_orchestrator = ProductOrchestrator(
    engines={
        "engine_1": content_engine,
        "engine_2": claims_engine,
        "engine_3": actions_engine,
        "engine_4": sources_engine,
        "engine_5": evidence_engine,
        "engine_6": threat_engine,
        "engine_7": fingerprint_engine,
        "engine_8": policy_engine,
        "engine_9": identity_engine,
        "engine_10": behaviour_engine,
    }
)


@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """Health status check."""
    return {
        "status": "healthy",
        "engine": "Nivesh Firewall Unified API",
        "unified_firewall_api": "/api/v1/firewall/analyze",
        "retrieval_api": "/api/v1/firewall/analysis/{analysis_id}",
        "engines": [
            "Engine 1: Content Intelligence Engine",
            "Engine 2: Claim Intelligence Engine",
            "Engine 3: Action Intelligence Engine",
            "Engine 4: Source Intelligence Engine",
            "Engine 5: Evidence Verification Engine",
            "Engine 6: Threat & Attack-Path Intelligence Engine",
            "Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine",
            "Engine 8: Policy & Intervention Engine",
            "Engine 9: Identity Verification & Entity Resolution Engine",
            "Engine 10: Behavioural Signal Intelligence Engine",
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


@app.post(
    "/api/v1/threat/analyze",
    response_model=ThreatAnalysis,
    tags=["Threat Intelligence (Engine 6)"],
    summary="Construct attack path, detect threat signals, and classify threat families"
)
async def analyze_threat(request: Request):
    """Consumes NormalizedContent, ClaimAnalysis, ActionAnalysis, SourceAnalysis, and EvidenceAnalysis to construct an attack path."""
    try:
        body = await request.json()
        if "content" in body:
            payload = ThreatAnalysisPayload(**body)
            content = payload.content
            claims = payload.claims
            actions = payload.actions
            sources = payload.sources
            evidence = payload.evidence
        else:
            content = NormalizedContent(**body)
            claims = None
            actions = None
            sources = None
            evidence = None

        # Auto-pipeline cascading if upstream stages omitted
        if claims is None:
            claims = claims_engine.analyze(content)
        if actions is None:
            actions = actions_engine.analyze(content, claims)
        if sources is None:
            sources = sources_engine.discover_and_retrieve(content, claims, actions)
        if evidence is None:
            evidence = evidence_engine.verify(content, claims, sources)

        return threat_engine.analyze(content, claims, actions, sources, evidence)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Threat analysis failed: {str(e)}"
        )


@app.post(
    "/api/v1/fingerprints/match",
    response_model=FingerprintAnalysis,
    tags=["Scam Fingerprint (Engine 7)"],
    summary="Match observation against collective threat fingerprints or register new pattern",
)
async def match_fingerprint(request: Request):
    """Consumes normalized content through ThreatAnalysis, matching against stored fingerprints."""
    try:
        body = await request.json()
        if "content" in body:
            payload = FingerprintMatchPayload(**body)
            content = payload.content
            claims = payload.claims
            actions = payload.actions
            sources = payload.sources
            evidence = payload.evidence
            threat = payload.threat
        else:
            content = NormalizedContent(**body)
            claims = None
            actions = None
            sources = None
            evidence = None
            threat = None

        if claims is None:
            claims = claims_engine.analyze(content)
        if actions is None:
            actions = actions_engine.analyze(content, claims)
        if sources is None:
            sources = sources_engine.discover_and_retrieve(content, claims, actions)
        if evidence is None:
            evidence = evidence_engine.verify(content, claims, sources)
        if threat is None:
            threat = threat_engine.analyze(content, claims, actions, sources, evidence)

        return fingerprint_engine.create_or_match(content, claims, actions, sources, evidence, threat)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Fingerprint matching failed: {str(e)}"
        )


@app.post(
    "/api/v1/fingerprints/create",
    response_model=ScamFingerprint,
    tags=["Scam Fingerprint (Engine 7)"],
    summary="Register a new scam fingerprint in collective memory",
)
async def create_fingerprint(request: Request):
    """Creates and registers a new ScamFingerprint into repository."""
    try:
        body = await request.json()
        if "fingerprint_id" in body and "exact_signature" in body:
            fp = ScamFingerprint(**body)
            return fingerprint_engine.repository.add_fingerprint(fp)

        if "content" in body:
            payload = FingerprintMatchPayload(**body)
            content = payload.content
            claims = payload.claims
            actions = payload.actions
            sources = payload.sources
            evidence = payload.evidence
            threat = payload.threat
        else:
            content = NormalizedContent(**body)
            claims = None
            actions = None
            sources = None
            evidence = None
            threat = None

        if claims is None:
            claims = claims_engine.analyze(content)
        if actions is None:
            actions = actions_engine.analyze(content, claims)
        if sources is None:
            sources = sources_engine.discover_and_retrieve(content, claims, actions)
        if evidence is None:
            evidence = evidence_engine.verify(content, claims, sources)
        if threat is None:
            threat = threat_engine.analyze(content, claims, actions, sources, evidence)

        features = fingerprint_engine.feature_extractor.extract_features(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence,
            threat=threat
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        new_fp = fingerprint_engine._create_new_fingerprint(features, now_iso)
        return fingerprint_engine.repository.add_fingerprint(new_fp)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Fingerprint creation failed: {str(e)}"
        )


@app.get(
    "/api/v1/fingerprints/search",
    response_model=list[ScamFingerprint],
    tags=["Scam Fingerprint (Engine 7)"],
    summary="Search stored fingerprints by query, status, threat family, or channel",
)
async def search_fingerprints(
    query: Optional[str] = None,
    status: Optional[str] = None,
    threat_family: Optional[str] = None,
    channel: Optional[str] = None,
):
    """Searches stored threat fingerprints in collective memory."""
    try:
        return fingerprint_engine.search_fingerprints(
            query=query,
            status=status,
            threat_family=threat_family,
            channel=channel,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Fingerprint search failed: {str(e)}"
        )


@app.get(
    "/api/v1/fingerprints/{fingerprint_id}",
    response_model=ScamFingerprint,
    tags=["Scam Fingerprint (Engine 7)"],
    summary="Retrieve details of a specific scam fingerprint",
)
async def get_fingerprint(fingerprint_id: str):
    """Retrieves a single scam fingerprint by ID."""
    fp = fingerprint_engine.get_fingerprint(fingerprint_id)
    if not fp:
        raise HTTPException(
            status_code=404,
            detail=f"Fingerprint '{fingerprint_id}' not found."
        )
    return fp


@app.post(
    "/api/v1/fingerprints/{fingerprint_id}/dispute",
    response_model=ScamFingerprint,
    tags=["Scam Fingerprint (Engine 7)"],
    summary="Record a dispute against a fingerprint",
)
async def dispute_fingerprint(fingerprint_id: str, payload: FingerprintDisputePayload):
    """Records a dispute note against a fingerprint and marks it DISPUTED."""
    fp = fingerprint_engine.dispute_fingerprint(fingerprint_id, reason=payload.reason, actor=payload.actor)
    if not fp:
        raise HTTPException(
            status_code=404,
            detail=f"Fingerprint '{fingerprint_id}' not found."
        )
    return fp


# ==============================================================================
# Engine 8: Policy & Intervention API Endpoints
# ==============================================================================

@app.post(
    "/api/v1/policy/decide",
    response_model=PolicyDecision,
    tags=["Policy & Intervention (Engine 8)"],
    summary="Evaluate safety policy and determine intervention level",
)
async def evaluate_policy(request: Request):
    """Determines the appropriate safety intervention based on multi-engine intelligence."""
    try:
        body = await request.json()
        if "content" in body:
            payload = PolicyDecidePayload(**body)
            content = payload.content
            claims = payload.claims
            actions = payload.actions
            sources = payload.sources
            evidence = payload.evidence
            threat = payload.threat
            fingerprint = payload.fingerprint
            identity = payload.identity
            behaviour = payload.behaviour
            context = payload.context
        else:
            content = NormalizedContent(**body)
            claims = None
            actions = None
            sources = None
            evidence = None
            threat = None
            fingerprint = None
            identity = None
            behaviour = None
            context = None

        if claims is None:
            claims = claims_engine.analyze(content)
        if actions is None:
            actions = actions_engine.analyze(content, claims)
        if sources is None:
            sources = sources_engine.discover_and_retrieve(content, claims, actions)
        if evidence is None:
            evidence = evidence_engine.verify(content, claims, sources)
        if threat is None:
            threat = threat_engine.analyze(content, claims, actions, sources, evidence)
        if fingerprint is None:
            fingerprint = fingerprint_engine.create_or_match(content, claims, actions, sources, evidence, threat)
        if identity is None:
            identity = identity_engine.verify(
                content=content,
                claims=claims,
                sources=sources,
                evidence=evidence,
                threat=threat,
            )
        if behaviour is None:
            behaviour = behaviour_engine.analyze(
                content=content,
                claims=claims,
                actions=actions,
                threat=threat,
                fingerprint=fingerprint,
                identity=identity,
            )

        decision = policy_engine.decide(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence,
            threat=threat,
            fingerprint=fingerprint,
            identity=identity,
            behaviour=behaviour,
            context=context,
        )
        return decision
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Policy evaluation failed: {str(e)}"
        )


@app.get(
    "/api/v1/policy/rules",
    tags=["Policy & Intervention (Engine 8)"],
    summary="List registered safety policy rules",
)
async def list_policy_rules():
    """Lists all active investor-protection policy rules."""
    return policy_engine.list_rules()


@app.get(
    "/api/v1/policy/{decision_id}",
    response_model=PolicyDecision,
    tags=["Policy & Intervention (Engine 8)"],
    summary="Retrieve a stored policy decision by ID",
)
async def get_policy_decision(decision_id: str):
    """Retrieves an existing policy decision record."""
    decision = policy_engine.get_decision(decision_id)
    if not decision:
        raise HTTPException(
            status_code=404,
            detail=f"Policy decision '{decision_id}' not found."
        )
    return decision


@app.post(
    "/api/v1/policy/explain",
    tags=["Policy & Intervention (Engine 8)"],
    summary="Get detailed user-facing and technical policy explanations",
)
async def explain_policy(request: Request):
    """Provides non-accusatory user and technical explanations for a decision or interaction."""
    try:
        body = await request.json()
        if "decision_id" in body:
            decision = policy_engine.get_decision(body["decision_id"])
            if not decision:
                raise HTTPException(
                    status_code=404,
                    detail=f"Policy decision '{body['decision_id']}' not found."
                )
            return {
                "decision_id": decision.decision_id,
                "decision": decision.decision,
                "severity": decision.severity,
                "primary_reason": decision.primary_reason,
                "user_message": decision.user_message,
                "technical_message": decision.technical_message,
                "reason_codes": decision.reason_codes,
                "supporting_reasons": decision.supporting_reasons,
                "required_user_confirmation": decision.required_user_confirmation,
            }
        
        # If payload is provided directly, evaluate and explain
        decision = await evaluate_policy(request)
        return {
            "decision_id": decision.decision_id,
            "decision": decision.decision,
            "severity": decision.severity,
            "primary_reason": decision.primary_reason,
            "user_message": decision.user_message,
            "technical_message": decision.technical_message,
            "reason_codes": decision.reason_codes,
            "supporting_reasons": decision.supporting_reasons,
            "required_user_confirmation": decision.required_user_confirmation,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Policy explanation failed: {str(e)}"
        )


# ============================================================================
# Engine 9: Identity Verification & Entity Resolution Endpoints
# ============================================================================

@app.post(
    "/api/v1/identity/verify",
    response_model=IdentityAnalysis,
    tags=["Identity Verification (Engine 9)"],
    summary="Verify entity identity consistency against authoritative evidence",
)
async def verify_identity(request: Request):
    """Verifies claimed entity identity consistency against authoritative registry records."""
    try:
        body = await request.json()
        payload = IdentityVerificationPayload(**body)

        content = payload.content
        if not content:
            raw_text = payload.text or body.get("raw_text") or body.get("text")
            if not raw_text:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'content' or 'text' must be provided in payload."
                )
            content = content_engine.process_text(raw_text)

        claims = payload.claims
        if not claims:
            claims = claims_engine.analyze(content)

        sources = payload.sources
        if not sources:
            actions = actions_engine.analyze(content, claims)
            sources = sources_engine.discover_and_retrieve(content, claims, actions)

        evidence = payload.evidence
        if not evidence:
            evidence = evidence_engine.verify(content, claims, sources)

        threat = payload.threat

        analysis = identity_engine.verify(
            content=content,
            claims=claims,
            sources=sources,
            evidence=evidence,
            threat=threat,
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Identity verification failed: {str(e)}"
        )


@app.get(
    "/api/v1/identity/{analysis_id}",
    response_model=IdentityAnalysis,
    tags=["Identity Verification (Engine 9)"],
    summary="Retrieve an identity analysis by ID",
)
async def get_identity_analysis(analysis_id: str):
    """Retrieves an existing identity analysis record from in-memory cache."""
    analysis = identity_engine.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Identity analysis '{analysis_id}' not found."
        )
    return analysis


@app.get(
    "/api/v1/identity/entities/{entity_id}",
    response_model=ClaimedEntity,
    tags=["Identity Verification (Engine 9)"],
    summary="Retrieve a claimed entity by ID",
)
async def get_identity_entity(entity_id: str):
    """Retrieves a claimed entity record from in-memory cache."""
    entity = identity_engine.get_entity(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Claimed entity '{entity_id}' not found."
        )
    return entity


# ==============================================================================
# Engine 10: Behavioural Signal Intelligence Endpoints
# ==============================================================================

@app.post(
    "/api/v1/behaviour/analyze",
    response_model=BehaviouralAnalysis,
    tags=["Behavioural Signal Intelligence (Engine 10)"],
    summary="Analyze interaction sequence for behavioural signals",
)
async def analyze_behaviour(request: Request):
    """Analyzes interaction events and content for behavioural and escalation patterns.

    Identifies time pressure, progressive commitment, channel transitions, and retries.
    Does not produce scam probabilities, psychological evaluations, or policy decisions.
    """
    try:
        body = await request.json()
        payload = BehaviouralAnalyzePayload(**body)

        content = payload.content
        if not content:
            raw_text = payload.text or body.get("raw_text") or body.get("text")
            if not raw_text:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'content' or 'text' must be provided in payload."
                )
            content = content_engine.process_text(raw_text)

        claims = payload.claims
        if not claims:
            claims = claims_engine.analyze(content)

        actions = payload.actions
        if not actions:
            actions = actions_engine.analyze(content, claims)

        analysis = behaviour_engine.analyze(
            content=content,
            claims=claims,
            actions=actions,
            threat=payload.threat,
            fingerprint=payload.fingerprint,
            identity=payload.identity,
            interaction_history=payload.interaction_history,
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Behavioural analysis failed: {str(e)}"
        )


@app.get(
    "/api/v1/behaviour/{analysis_id}",
    response_model=BehaviouralAnalysis,
    tags=["Behavioural Signal Intelligence (Engine 10)"],
    summary="Retrieve a behavioural analysis record by ID",
)
async def get_behaviour_analysis(analysis_id: str):
    """Retrieves an existing behavioural analysis record from in-memory cache."""
    analysis = behaviour_engine.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Behavioural analysis '{analysis_id}' not found."
        )
    return analysis


@app.post(
    "/api/v1/behaviour/events",
    tags=["Behavioural Signal Intelligence (Engine 10)"],
    summary="Record an interaction event into session history",
)
async def record_behaviour_event(payload: BehaviouralEventPayload):
    """Appends a structured, privacy-safe interaction event to the specified session."""
    try:
        history = behaviour_engine.record_event(payload.session_id, payload.event)
        return {
            "status": "recorded",
            "session_id": history.session_id,
            "event_count": history.event_count,
            "last_event_at": history.last_event_at,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to record interaction event: {str(e)}"
        )


# ==============================================================================
# Unified Nivesh Firewall Product API (Phase 11.4)
# ==============================================================================

MAX_TEXT_LENGTH = 50_000
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_SESSION_ID_LENGTH = 128


@app.post(
    "/api/v1/firewall/analyze",
    response_model=FirewallAnalysisResponse,
    responses={
        400: {"model": FirewallApiError, "description": "Invalid client request or input payload"},
        500: {"model": FirewallApiError, "description": "Internal pipeline execution failure"},
    },
    tags=["Nivesh Firewall (Unified Product API)"],
    summary="Execute unified end-to-end Nivesh Firewall security analysis",
)
async def firewall_analyze(payload: FirewallAnalyzeRequest):
    """Execute end-to-end security analysis across Engines 1 through 10.

    Canonical frontend-facing API endpoint. Returns unified decision from Engine 8
    along with structured summaries for claims, actions, evidence, identity,
    threat, fingerprint, and behavioural patterns. Does not expose credentials or PII.
    """
    # 1. Validate Input Type
    if payload.input_type not in ("text", "url", "image"):
        return JSONResponse(
            status_code=400,
            content=FirewallApiError(
                error_code="UNSUPPORTED_INPUT",
                message=f"Unsupported input type '{payload.input_type}'. Must be 'text', 'url', or 'image'.",
                details={"input_type": payload.input_type, "supported": ["text", "url", "image"]},
            ).model_dump(),
        )

    # 2. Check for empty payload
    has_text = bool(payload.text and payload.text.strip())
    has_url = bool(payload.url and payload.url.strip())
    has_image = bool(payload.image_base64 or payload.image_path)

    if not has_text and not has_url and not has_image:
        return JSONResponse(
            status_code=400,
            content=FirewallApiError(
                error_code="INVALID_REQUEST",
                message="No valid input provided. Specify 'text', 'url', or 'image_base64'.",
                details={"supported_fields": ["text", "url", "image_base64", "image_path"]},
            ).model_dump(),
        )

    # 3. Payload size checks
    if payload.text and len(payload.text) > MAX_TEXT_LENGTH:
        return JSONResponse(
            status_code=400,
            content=FirewallApiError(
                error_code="INPUT_TOO_LARGE",
                message=f"Payload text exceeds maximum permitted limit of {MAX_TEXT_LENGTH} characters.",
                details={"provided_length": len(payload.text), "max_limit": MAX_TEXT_LENGTH},
            ).model_dump(),
        )

    # 4. URL Validation
    if payload.url:
        parsed = urlparse(payload.url.strip())
        if not parsed.scheme or parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            return JSONResponse(
                status_code=400,
                content=FirewallApiError(
                    error_code="INVALID_URL",
                    message="Target URL is malformed or uses an unsupported protocol.",
                    details={"url": payload.url, "supported_schemes": ["http", "https"]},
                ).model_dump(),
            )

    # 5. Session ID Validation
    if payload.session_id and len(payload.session_id) > MAX_SESSION_ID_LENGTH:
        return JSONResponse(
            status_code=400,
            content=FirewallApiError(
                error_code="INVALID_SESSION",
                message=f"Session identifier exceeds maximum length of {MAX_SESSION_ID_LENGTH} characters.",
                details={"session_id_length": len(payload.session_id), "max_limit": MAX_SESSION_ID_LENGTH},
            ).model_dump(),
        )

    # 6. Decode Base64 Image
    image_bytes = None
    if payload.image_base64:
        try:
            image_bytes = base64.b64decode(payload.image_base64)
            if len(image_bytes) > MAX_IMAGE_BYTES:
                return JSONResponse(
                    status_code=400,
                    content=FirewallApiError(
                        error_code="INPUT_TOO_LARGE",
                        message=f"Image payload exceeds maximum limit of {MAX_IMAGE_BYTES // (1024*1024)}MB.",
                        details={"provided_bytes": len(image_bytes), "max_bytes": MAX_IMAGE_BYTES},
                    ).model_dump(),
                )
        except Exception:
            return JSONResponse(
                status_code=400,
                content=FirewallApiError(
                    error_code="INVALID_REQUEST",
                    message="Failed to decode base64 image data.",
                    details={},
                ).model_dump(),
            )

    # 7. Execute Orchestration
    try:
        result = firewall_orchestrator.analyze(
            text=payload.text,
            url=payload.url,
            image_bytes=image_bytes,
            image_path=payload.image_path,
            session_id=payload.session_id,
            interaction_history=payload.interaction_history,
            metadata=payload.metadata,
            channel=payload.channel,
            policy_context=payload.policy_context,
            idempotency_key=payload.idempotency_key,
        )
        response = firewall_orchestrator.format_response(result)
        return response
    except Exception as e:
        # Sanitized error response - no stack trace or filesystem paths exposed
        return JSONResponse(
            status_code=500,
            content=FirewallApiError(
                error_code="PIPELINE_FAILURE",
                message="An unexpected error occurred during firewall analysis execution.",
                details={"engine": "ProductOrchestrator"},
            ).model_dump(),
        )


@app.get(
    "/api/v1/firewall/analysis/{analysis_id}",
    response_model=FirewallAnalysisResponse,
    responses={
        404: {"model": FirewallApiError, "description": "Analysis record not found"},
        500: {"model": FirewallApiError, "description": "Internal error during retrieval"},
    },
    tags=["Nivesh Firewall (Unified Product API)"],
    summary="Retrieve unified firewall analysis result by analysis ID",
)
async def get_firewall_analysis(analysis_id: str):
    """Retrieve a previously executed Nivesh Firewall analysis.

    Preserves privacy sanitization, final policy decision, and provenance
    without re-running the underlying intelligence pipeline.
    """
    try:
        result = firewall_orchestrator.get_analysis(analysis_id)
        if not result:
            return JSONResponse(
                status_code=404,
                content=FirewallApiError(
                    error_code="ANALYSIS_NOT_FOUND",
                    message=f"Analysis with ID '{analysis_id}' was not found.",
                    analysis_id=analysis_id,
                    details={"reason": "The requested analysis ID does not exist or has expired."},
                ).model_dump(),
            )
        response = firewall_orchestrator.format_response(result)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=FirewallApiError(
                error_code="PIPELINE_FAILURE",
                message="An unexpected error occurred while retrieving analysis.",
                analysis_id=analysis_id,
                details={},
            ).model_dump(),
        )






