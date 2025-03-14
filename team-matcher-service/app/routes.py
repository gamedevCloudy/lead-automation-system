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
    """Match a lead to team members based on relevance"""
    try:
        # Get lead data and find matching team members
        match_result = await matcher_service.match_team_to_lead(lead_id, request.analysis_context)
        return match_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match team: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "team-matcher"}

@router.get("/team-members", response_model=List[Dict[str, Any]])
async def get_team_members(
    matcher_service: MatcherService = Depends(get_matcher_service)
):
    """Get all team members from the database service"""
    try:
        team_members = await matcher_service.get_team_members()
        return team_members
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team members: {str(e)}")

@router.post("/notify/{lead_id}")
async def notify_team(
    lead_id: int,
    team_member_ids: List[int],
    matcher_service: MatcherService = Depends(get_matcher_service)
):
    """Notify matched team members about a new lead"""
    try:
        # Get lead data
        lead_data = await matcher_service.get_lead_data(lead_id)
        
        # Prepare data for email service
        email_data = {
            "lead_id": lead_id,
            "lead_info": lead_data,
            "team_member_ids": team_member_ids
        }
        
        # Send notification request to email service
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{EMAIL_SERVICE_URL}/send-team-notification", json=email_data)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to notify team members: {response.text}"
                )
            
            return {"status": "success", "message": "Team members notified successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to notify team: {str(e)}")