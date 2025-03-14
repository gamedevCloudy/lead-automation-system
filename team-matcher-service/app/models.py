# team-matcher-service/app/models.py
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class MatchRequest(BaseModel):
    """Request for matching a lead to team members"""
    analysis_context: Optional[Dict[str, Any]] = None

class TeamMemberMatch(BaseModel):
    """Information about a matched team member"""
    team_member_id: int
    name: str
    email: str
    role: str
    relevance_score: float
    matching_reasons: List[str]

class MatchResult(BaseModel):
    """Result of the team matching process"""
    lead_id: int
    matches: List[TeamMemberMatch]