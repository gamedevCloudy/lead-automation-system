# database-service/app/models.py
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

Base = declarative_base()

# SQLAlchemy Models
class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    position = Column(String)
    email = Column(String, nullable=False)
    phone = Column(String)
    revenue = Column(Float)
    service_type = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analyses = relationship("Analysis", back_populates="lead")
    team_matches = relationship("TeamMatch", back_populates="lead")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    skills = Column(JSON)  # List of skills
    role = Column(String)
    expertise_summary = Column(Text)
    always_notify = Column(Boolean, default=False)
    
    team_matches = relationship("TeamMatch", back_populates="team_member")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    company_details = Column(JSON)
    llm_analysis = Column(Text)
    final_decision = Column(String)  # "Yes", "No", "Maybe"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="analyses")

class TeamMatch(Base):
    __tablename__ = "team_matches"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    team_member_id = Column(Integer, ForeignKey("team_members.id"))
    relevance_score = Column(Float)  # A score indicating how well the team member matches the lead
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="team_matches")
    team_member = relationship("TeamMember", back_populates="team_matches")

# Pydantic Models
class LeadBase(BaseModel):
    company_name: str
    contact_name: str
    position: Optional[str] = None
    email: str
    phone: Optional[str] = None
    revenue: Optional[float] = None
    service_type: Optional[str] = None
    message: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class Lead(LeadBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class TeamMemberBase(BaseModel):
    name: str
    email: str
    skills: List[str]
    role: str
    expertise_summary: str
    always_notify: bool = False

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMember(TeamMemberBase):
    id: int

    class Config:
        orm_mode = True

class AnalysisBase(BaseModel):
    lead_id: int
    company_details: Dict[str, Any]
    llm_analysis: str
    final_decision: str

class AnalysisCreate(AnalysisBase):
    pass

class Analysis(AnalysisBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class TeamMatchBase(BaseModel):
    lead_id: int
    team_member_id: int
    relevance_score: float

class TeamMatchCreate(TeamMatchBase):
    pass

class TeamMatch(TeamMatchBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True