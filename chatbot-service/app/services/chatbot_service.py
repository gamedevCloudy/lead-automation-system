# chatbot-service/app/services/chatbot_service.py
import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Tuple, Optional

class ChatbotService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        
        # Create a model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Define conversation prompts
        self.system_prompt = """
        You are a friendly AI assistant for a digital marketing and web development agency.
        Your task is to engage with potential leads who visit our website and collect important information.
        
        You should collect the following information:
        - Company name
        - Lead's name and position
        - Revenue (approximate is fine)
        - Contact information (email is mandatory, phone is optional)
        - Type of service they are looking for
        
        Be conversational and helpful. Don't ask for all information at once. Collect it naturally throughout the conversation.
        After each response, you will analyze what information has been collected and what is still missing.
        
        In addition to collecting information, provide value by answering any questions they might have about our services.
        
        MOST IMPORTANT: You must extract and structure the information from the conversation to be stored in our database.
        """
        
        self.extraction_prompt = """
        Based on the conversation so far, extract the following information about the lead:
        - company_name: The name of the company
        - contact_name: The full name of the contact person
        - position: Their job title or position
        - email: Their email address
        - phone: Their phone number (if provided)
        - revenue: Their approximate annual revenue (as a number if possible)
        - service_type: What service they're interested in
        - message: Any additional details about their needs
        
        Return ONLY a valid JSON object with these fields. Use null for missing values.
        If you can't determine a particular value with confidence, use null.
        """

    async def process_chat(self, messages: List[Dict[str, str]]) -> Tuple[str, Optional[Dict[str, Any]]]:
        # Prepare messages for Gemini
        gemini_messages = []
        
        # Add system prompt
        gemini_messages.append({"role": "user", "parts": [self.system_prompt]})
        gemini_messages.append({"role": "model", "parts": ["I understand my role. I'll engage with potential leads in a friendly, conversational manner while collecting the necessary information gradually. I'll be ready to answer questions about your services while extracting key data for your database."]})
        
        # Add user messages
        for message in messages:
            # Fix: Access the message object as a Pydantic model using attribute notation
            gemini_messages.append({
                "role": "user" if message.role == "user" else "model",
                "parts": [message.content]
            })
        
        # Get response from Gemini
        chat = self.model.start_chat(history=gemini_messages)
        response = await chat.send_message_async("Please respond to the user's latest message")
        
        # Extract structured information
        extraction_response = await chat.send_message_async(self.extraction_prompt)
        
        # Parse the extracted JSON
        extracted_data = None
        try:
            # Clean the response to get only the JSON part
            json_text = extraction_response.text
            
            # Handle cases where the JSON might be wrapped in code blocks
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
                
            extracted_data = json.loads(json_text)
        except Exception as e:
            print(f"Error extracting data: {str(e)}")
            extracted_data = {}
        
        return response.text, extracted_data