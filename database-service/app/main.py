# database-service/app/main.py
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any

from .database import get_db, init_db
from .models import (
    LeadBase, LeadCreate, Lead, 
    TeamMemberBase, TeamMemberCreate, TeamMember,
    AnalysisBase, AnalysisCreate, Analysis,
    TeamMatchBase, TeamMatchCreate, TeamMatch
)

app = FastAPI(title="Lead Automation Database Service")

@app.on_event("startup")
async def startup():
    await init_db()

# Lead Routes
@app.post("/leads/", response_model=Lead)
async def create_lead(lead: LeadCreate, db: AsyncSession = Depends(get_db)):
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    await db.commit()
    await db.refresh(db_lead)
    return db_lead

@app.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.get("/leads/", response_model=List[Lead])
async def get_leads(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).offset(skip).limit(limit))
    return result.scalars().all()

# Team Member Routes
@app.post("/team-members/", response_model=TeamMember)
async def create_team_member(team_member: TeamMemberCreate, db: AsyncSession = Depends(get_db)):
    db_team_member = TeamMember(**team_member.dict())
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@app.get("/team-members/{team_member_id}", response_model=TeamMember)
async def get_team_member(team_member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).where(TeamMember.id == team_member_id))
    team_member = result.scalars().first()
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return team_member

@app.get("/team-members/", response_model=List[TeamMember])
async def get_team_members(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).offset(skip).limit(limit))
    return result.scalars().all()

# Analysis Routes
@app.post("/analyses/", response_model=Analysis)
async def create_analysis(analysis: AnalysisCreate, db: AsyncSession = Depends(get_db)):
    db_analysis = Analysis(**analysis.dict())
    db.add(db_analysis)
    await db.commit()
    await db.refresh(db_analysis)
    return db_analysis

@app.get("/analyses/{lead_id}", response_model=Analysis)
async def get_analysis_by_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Analysis).where(Analysis.lead_id == lead_id))
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

# Team Match Routes
@app.post("/team-matches/", response_model=TeamMatch)
async def create_team_match(team_match: TeamMatchCreate, db: AsyncSession = Depends(get_db)):
    db_team_match = TeamMatch(**team_match.dict())
    db.add(db_team_match)
    await db.commit()
    await db.refresh(db_team_match)
    return db_team_match

@app.get("/team-matches/{lead_id}", response_model=List[TeamMatch])
async def get_team_matches_by_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMatch).where(TeamMatch.lead_id == lead_id))
    matches = result.scalars().all()
    return matches

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)