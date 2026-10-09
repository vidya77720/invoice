import httpx
from typing import Optional, Dict, Any
import json

from app.core.config import settings

class AIService:
    """Service for AI-powered invoice data extraction"""
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def extract_invoice_data(self, invoice_text: str) -> Dict[str, Any]:
        """Extract invoice data using LLM"""
        
        prompt = f"""Extract invoice information from the following text. Return ONLY a JSON object with these exact keys. If a value is not found, use null.

Text:
{invoice_text}

Return JSON with these keys:
- vendor_name (string)
- vendor_address (string)
- gstin (string)
- invoice_number (string)
- invoice_date (YYYY-MM-DD format)
- due_date (YYYY-MM-DD format)
- currency (string, default INR)
- subtotal (number)
- discount (number)
- tax_amount (number)
- total_amount (number)
- line_items (array of objects with: description, quantity, unit_price, tax_rate, amount)

IMPORTANT:
- Return ONLY the JSON, no other text
- Use null for missing values, never invent values
- Dates must be in YYYY-MM-DD format
- Amounts should be numbers, not strings
- Do not include currency symbols in amount values"""

        try:
            if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
                return self._call_openai(prompt)
            elif settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
                return self._call_anthropic(prompt)
            else:
                # Return empty extraction if no API key
                return self._get_empty_extraction()
                
        except Exception as e:
            print(f"AI extraction error: {str(e)}")
            return self._get_empty_extraction()
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        response = self.client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are an invoice data extractor. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API"""
        response = self.client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]
            return self._parse_json_response(content)
        else:
            raise Exception(f"Anthropic API error: {response.status_code}")
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Try to extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except json.JSONDecodeError:
            # If parsing fails, return empty extraction
            return self._get_empty_extraction()
    
    def _get_empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction structure"""
        return {
            "vendor_name": None,
            "vendor_address": None,
            "gstin": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "currency": "INR",
            "subtotal": None,
            "discount": 0,
            "tax_amount": None,
            "total_amount": None,
            "line_items": []
        }
    
    def categorize_expense(self, invoice_data: Dict[str, Any]) -> str:
        """Categorize expense based on invoice data"""
        
        if not invoice_data.get("vendor_name") and not invoice_data.get("line_items"):
            return "Other"
        
        vendor_name = (invoice_data.get("vendor_name") or "").lower()
        line_items = invoice_data.get("line_items", [])
        
        # Check line items for keywords
        item_descriptions = " ".join([item.get("description", "") for item in line_items]).lower()
        
        # Category keywords
        software_keywords = ["software", "saas", "subscription", "cloud", "api", "license", "microsoft", "google", "amazon", "azure"]
        travel_keywords = ["flight", "hotel", "travel", "taxi", "uber", "ola", "transport", "accommodation"]
        marketing_keywords = ["marketing", "advertising", "promotion", "social media", "facebook", "google ads"]
        office_keywords = ["office", "stationery", "furniture", "supplies", "paper", "printer"]
        utility_keywords = ["electricity", "water", "internet", "phone", "utility", "gas"]
        equipment_keywords = ["laptop", "computer", "hardware", "equipment", "machine", "device"]
        logistics_keywords = ["shipping", "delivery", "courier", "freight", "transport", "logistics"]
        professional_keywords = ["consulting", "legal", "accounting", "audit", "professional", "services"]
        
        # Check category based on keywords
        all_text = f"{vendor_name} {item_descriptions}"
        
        if any(keyword in all_text for keyword in software_keywords):
            return "Software & Technology"
        elif any(keyword in all_text for keyword in travel_keywords):
            return "Travel"
        elif any(keyword in all_text for keyword in marketing_keywords):
            return "Marketing"
        elif any(keyword in all_text for keyword in office_keywords):
            return "Office Supplies"
        elif any(keyword in all_text for keyword in utility_keywords):
            return "Utilities"
        elif any(keyword in all_text for keyword in equipment_keywords):
            return "Equipment"
        elif any(keyword in all_text for keyword in logistics_keywords):
            return "Logistics"
        elif any(keyword in all_text for keyword in professional_keywords):
            return "Professional Services"
        else:
            return "Other"
    
    def close(self):
        """Close HTTP client"""
        self.client.close()

ai_service = AIService()
