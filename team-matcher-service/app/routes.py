# team-matcher-service/app/routes.py
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from .models import MatchRequest, MatchResult, TeamMemberMatch
from .services.matcher_service import MatcherService

router = APIRouter()

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8000")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8004")

async def get_matcher_service():
    return MatcherService()

@router.post("/match/{lead_id}", response_model=MatchResult)
async def match_team(
    lead_id: int,
    request: MatchRequest,
    matcher_service: MatcherService = Depends(get_matcher_service)
):
    # Get lead data from database service
    return