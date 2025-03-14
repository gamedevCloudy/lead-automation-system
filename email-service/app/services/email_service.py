# app/services/email_service.py
import os
import aiosmtplib
import httpx
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure email parameters
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
EMAIL_FROM = os.environ.get("EMAIL_FROM")

# Configure service URLs
DATABASE_SERVICE_URL = os.environ.get("DATABASE_SERVICE_URL")
TEAM_MATCHER_URL = os.environ.get("TEAM_MATCHER_URL")

# Configure Jinja2 environment
template_env = Environment(loader=FileSystemLoader("app/templates"))


class EmailService:
    async def get_lead_details(self, lead_id: int) -> Dict[str, Any]:
        """Fetch lead details from the database service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{DATABASE_SERVICE_URL}/leads/{lead_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching lead details: {str(e)}")
                raise HTTPException(status_code=404, detail=f"Lead not found: {str(e)}")

    async def get_lead_analysis(self, lead_id: int) -> Dict[str, Any]:
        """Fetch lead analysis from the database service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{DATABASE_SERVICE_URL}/analyses/{lead_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching lead analysis: {str(e)}")
                return {"company_details": "Not available", "llm_analysis": "Not available", "final_decision": "Unknown"}

    async def get_matched_team_members(self, lead_id: int) -> List[Dict[str, Any]]:
        """Fetch matched team members from the team-matcher service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{TEAM_MATCHER_URL}/match/{lead_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching matched team members: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error fetching team members: {str(e)}")

    async def get_default_recipients(self) -> List[Dict[str, Any]]:
        """Fetch default recipients who always receive briefs"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{DATABASE_SERVICE_URL}/team-members/default-recipients")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching default recipients: {str(e)}")
                return []

    async def generate_email_subject(self, lead_details: Dict[str, Any]) -> str:
        """Generate an email subject using Gemini AI"""
        prompt = f"""
        Create a concise, professional email subject line for a new lead brief. 
        The company is {lead_details['company_name']} and they're interested in {lead_details['service_type']}.
        Make it attention-grabbing but professional. Don't use exclamation marks.
        Only return the subject line text with no additional commentary.
        """
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            subject = response.text.strip()
            # Ensure subject isn't too long
            if len(subject) > 78:
                subject = subject[:75] + "..."
            return subject
        except Exception as e:
            logger.error(f"Error generating email subject: {str(e)}")
            return f"New Lead Brief: {lead_details['company_name']}"

    async def generate_email_content(self, lead_details: Dict[str, Any], lead_analysis: Dict[str, Any]) -> str:
        """Generate personalized email content using Gemini AI"""
        prompt = f"""
        Generate a professional, concise email body for an internal team about a new lead. 
        Include these details in a well-formatted way:
        
        Company: {lead_details['company_name']}
        Contact: {lead_details['lead_name']}, {lead_details['lead_position']}
        Email: {lead_details['contact_email']}
        Phone: {lead_details.get('contact_phone', 'Not provided')}
        Service Interest: {lead_details.get('service_type', 'Not specified')}
        Revenue: {lead_details.get('revenue', 'Not provided')}
        
        Company Analysis: {lead_analysis.get('company_details', 'Not available')}
        Recommendation: {lead_analysis.get('final_decision', 'Not available')}
        
        Return only the HTML email content. Make it professional, clean, and well-structured.
        This is an internal email. No signatures, greetings, or email headers needed.
        """
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            # Fallback content if AI generation fails
            return f"""
            <h2>New Lead: {lead_details['company_name']}</h2>
            <p><strong>Contact:</strong> {lead_details['lead_name']}, {lead_details['lead_position']}</p>
            <p><strong>Email:</strong> {lead_details['contact_email']}</p>
            <p><strong>Service Interest:</strong> {lead_details.get('service_type', 'Not specified')}</p>
            
            <h3>Analysis</h3>
            <p>{lead_analysis.get('llm_analysis', 'Not available')}</p>
            <p><strong>Recommendation:</strong> {lead_analysis.get('final_decision', 'Not available')}</p>
            """

    async def render_email_template(self, lead_details: Dict[str, Any], lead_analysis: Dict[str, Any], 
                                   additional_content: Optional[str] = None) -> str:
        """Render the email template with all the data"""
        template = template_env.get_template("email_template.html")
        
        # Generate AI content if no additional content is provided
        ai_content = ""
        if not additional_content:
            ai_content = await self.generate_email_content(lead_details, lead_analysis)
        
        context = {
            "lead": lead_details,
            "analysis": lead_analysis,
            "additional_content": additional_content,
            "ai_content": ai_content
        }
        
        return template.render(**context)

    async def send_email(self, recipients: List[str], subject: str, html_content: str, 
                         cc_emails: Optional[List[str]] = None) -> bool:
        """Send email using configured SMTP server"""
        if not recipients:
            logger.warning("No recipients provided for email")
            return False
            
        message = MIMEMultipart("alternative")
        message["From"] = EMAIL_FROM
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        
        if cc_emails:
            message["Cc"] = ", ".join(cc_emails)
            
        message.attach(MIMEText(html_content, "html"))
        
        try:
            smtp = aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=True)
            await smtp.connect()
            await smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            all_recipients = recipients.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
                
            await smtp.send_message(message, recipients=all_recipients)
            await smtp.quit()
            
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def process_lead_email(self, lead_id: int, subject: Optional[str] = None, 
                               additional_content: Optional[str] = None,
                               cc_emails: Optional[List[str]] = None,
                               include_default_recipients: bool = True) -> Dict[str, Any]:
        """Process and send email for a lead"""
        # Get all required data
        lead_details = await self.get_lead_details(lead_id)
        lead_analysis = await self.get_lead_analysis(lead_id)
        matched_team_members = await self.get_matched_team_members(lead_id)
        
        # Get default recipients if needed
        default_recipients = []
        if include_default_recipients:
            default_recipients = await self.get_default_recipients()
        
        # Combine all recipients
        recipients = [member["email"] for member in matched_team_members]
        recipients.extend([member["email"] for member in default_recipients])
        # Remove duplicates while preserving order
        recipients = list(dict.fromkeys(recipients))
        
        # Generate subject if not provided
        if not subject:
            subject = await self.generate_email_subject(lead_details)
            
        # Render the email template
        html_content = await self.render_email_template(
            lead_details, 
            lead_analysis,
            additional_content
        )
        
        # Send the email
        success = await self.send_email(recipients, subject, html_content, cc_emails)
        
        return {
            "success": success,
            "message": "Email sent successfully" if success else "Failed to send email",
            "recipients": recipients
        }