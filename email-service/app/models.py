# app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class TeamMember(BaseModel):
    name: str
    email: EmailStr
    skills: List[str]
    role: str
    expertise_summary: str


class LeadDetails(BaseModel):
    id: int
    company_name: str
    lead_name: str
    lead_position: str
    revenue: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    service_type: Optional[str] = None
    additional_notes: Optional[str] = None
    
    
class LeadAnalysis(BaseModel):
    lead_id: int
    company_details: str
    llm_analysis: str
    final_decision: str
    
    
class EmailRequest(BaseModel):
    lead_id: int
    subject: Optional[str] = None
    additional_content: Optional[str] = None
    cc_emails: Optional[List[EmailStr]] = Field(default_factory=list)
    include_default_recipients: bool = True


class EmailResponse(BaseModel):
    success: bool
    message: str
    recipients: List[EmailStr]