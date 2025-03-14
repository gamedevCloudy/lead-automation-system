# app/routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
import logging

from app.models import EmailRequest, EmailResponse
from app.services.email_service import EmailService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(lambda: EmailService())
):
    """
    Send an email about a lead to matched team members
    
    - **lead_id**: ID of the lead to send email about
    - **subject**: Optional custom subject line
    - **additional_content**: Optional additional content to include
    - **cc_emails**: Optional list of emails to CC
    - **include_default_recipients**: Whether to include default recipients
    """
    try:
        result = await email_service.process_lead_email(
            lead_id=request.lead_id,
            subject=request.subject,
            additional_content=request.additional_content,
            cc_emails=request.cc_emails,
            include_default_recipients=request.include_default_recipients
        )
        return result
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@router.post("/send/background", response_model=EmailResponse)
async def send_email_background(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(lambda: EmailService())
):
    """
    Send an email about a lead to matched team members in the background
    
    This endpoint returns immediately and processes the email in the background
    """
    async def process_email_task():
        try:
            await email_service.process_lead_email(
                lead_id=request.lead_id,
                subject=request.subject,
                additional_content=request.additional_content,
                cc_emails=request.cc_emails,
                include_default_recipients=request.include_default_recipients
            )
        except Exception as e:
            logger.error(f"Background email task error: {str(e)}")
    
    background_tasks.add_task(process_email_task)
    
    return {
        "success": True,
        "message": "Email task added to background processing queue",
        "recipients": []  # Can't know recipients yet as it's processed in background
    }

@router.get("/template-preview/{lead_id}")
async def preview_email_template(
    lead_id: int,
    additional_content: Optional[str] = None,
    email_service: EmailService = Depends(lambda: EmailService())
):
    """Preview the email template for a lead without sending it"""
    try:
        lead_details = await email_service.get_lead_details(lead_id)
        lead_analysis = await email_service.get_lead_analysis(lead_id)
        
        html_content = await email_service.render_email_template(
            lead_details, 
            lead_analysis,
            additional_content
        )
        
        return {"html_content": html_content}
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error previewing template: {str(e)}")