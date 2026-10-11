import base64
import httpx
import json
import logging
from typing import Optional, Dict, Any

import pymupdf  # PyMuPDF — used to render PDF pages to images for Gemini Vision

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered invoice data extraction.

    Provider priority (auto-detected from .env):
      1. Gemini (Google)  — supports Vision; can extract from scanned PDFs
      2. OpenAI           — text only (needs pre-extracted text)
      3. Anthropic        — text only (needs pre-extracted text)
      4. Heuristic regex  — always available, works on digital PDFs
    """

    def __init__(self):
        self.client = httpx.Client(timeout=60.0)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def extract_invoice_data(self, invoice_text: str, file_path: str = None) -> Dict[str, Any]:
        """Extract invoice data using best available provider.

        Parameters
        ----------
        invoice_text : str
            Pre-extracted text (may be empty for scanned PDFs).
        file_path : str | None
            Path to the original file — used by Gemini Vision for image-based extraction.
        """
        try:
            # --- Gemini Vision (best for scanned PDFs) ---
            if settings.GEMINI_API_KEY:
                return self._call_gemini(invoice_text, file_path)

            # --- OpenAI text ---
            if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY and invoice_text.strip():
                return self._call_openai(self._build_text_prompt(invoice_text))

            # --- Anthropic text ---
            if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY and invoice_text.strip():
                return self._call_anthropic(self._build_text_prompt(invoice_text))

            # --- Heuristic fallback ---
            return self._heuristic_extraction(invoice_text)

        except Exception as e:
            logger.warning("AI extraction error, falling back to heuristic: %s", e)
            return self._heuristic_extraction(invoice_text)

    # ------------------------------------------------------------------ #
    # Gemini (supports Vision + text)
    # ------------------------------------------------------------------ #

    def _call_gemini(self, invoice_text: str, file_path: str = None) -> Dict[str, Any]:
        """Call Google Gemini API using the NEW google-genai SDK.
        Supports Vision — renders scanned PDFs to images for extraction.
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise Exception(
                "google-genai not installed. Run: pip install google-genai"
            )

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Models confirmed active and responsive for this API key
        MODELS_TO_TRY = [
            "gemini-flash-lite-latest",
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-latest",
        ]

        # Build content parts
        content_parts = []

        # Add rendered PDF/image for Vision
        if file_path:
            img_b64, mime = self._pdf_or_image_to_base64(file_path)
            if img_b64:
                import base64
                content_parts.append(
                    types.Part.from_bytes(
                        data=base64.b64decode(img_b64),
                        mime_type=mime
                    )
                )

        # Add text prompt
        prompt_text = self._build_text_prompt(
            invoice_text.strip() if invoice_text and invoice_text.strip()
            else "[See attached image — extract all invoice fields accurately]"
        )
        content_parts.append(prompt_text)

        last_error = None
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=content_parts,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=2048
                    )
                )
                text = response.text
                logger.info("Gemini SDK (google-genai) succeeded with model=%s", model_name)
                return self._parse_json_response(text)
            except Exception as e:
                last_error = f"{model_name}: {e}"
                logger.debug("Gemini model %s failed: %s", model_name, e)
                continue

        raise Exception(f"All Gemini models failed. Last error: {last_error}")

    def _pdf_or_image_to_base64(self, file_path: str) -> tuple[str, str]:
        """Render first page of PDF (or whole image) to PNG base64 for Gemini Vision."""
        import os
        from pathlib import Path

        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")

        try:
            if ext == "pdf":
                doc = pymupdf.open(str(path))
                page = doc[0]
                # Render at 2x scale for better OCR quality
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                doc.close()
                return base64.b64encode(img_bytes).decode(), "image/png"
            elif ext in ("jpg", "jpeg"):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode(), "image/jpeg"
            elif ext == "png":
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode(), "image/png"
        except Exception as e:
            logger.warning("Could not convert file to base64 for Gemini Vision: %s", e)

        return "", "image/png"

    # ------------------------------------------------------------------ #
    # OpenAI
    # ------------------------------------------------------------------ #

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI GPT API (text only)."""
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
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        raise Exception(f"OpenAI API error: {response.status_code}")

    # ------------------------------------------------------------------ #
    # Anthropic
    # ------------------------------------------------------------------ #

    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic Claude API (text only)."""
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
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        if response.status_code == 200:
            content = response.json()["content"][0]["text"]
            return self._parse_json_response(content)
        raise Exception(f"Anthropic API error: {response.status_code}")

    # ------------------------------------------------------------------ #
    # Shared prompt builder
    # ------------------------------------------------------------------ #

    def _build_text_prompt(self, invoice_text: str) -> str:
        return f"""Extract invoice information from the following text (or image if provided). 
Return ONLY a JSON object with these exact keys. If a value is not found, use null.

Text:
{invoice_text}

Return JSON with these keys:
- vendor_name (string)
- vendor_address (string)
- gstin (string, Indian GST format)
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
- Return ONLY valid JSON, no markdown, no explanation
- Use null for missing values, never invent values
- Dates must be in YYYY-MM-DD format
- Amounts should be numbers (no currency symbols)"""

    # ------------------------------------------------------------------ #
    # JSON parser
    # ------------------------------------------------------------------ #

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, stripping markdown fences if present."""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Could not parse JSON from LLM response — using empty extraction.")
            return self._get_empty_extraction()

    def _get_empty_extraction(self) -> Dict[str, Any]:
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

    # ------------------------------------------------------------------ #
    # Heuristic / Regex fallback (no API required)
    # ------------------------------------------------------------------ #

    def _heuristic_extraction(self, invoice_text: str) -> Dict[str, Any]:
        """Regex extraction when no LLM API is configured or text is available."""
        import re
        extracted = self._get_empty_extraction()
        if not invoice_text or not invoice_text.strip():
            return extracted

        lines = [line.strip() for line in invoice_text.splitlines() if line.strip()]

        # Vendor name
        for line in lines[:5]:
            m = re.search(r'(?:From|Vendor|Seller|Billed By)\s*[:\-]\s*(.+)', line, re.IGNORECASE)
            if m:
                extracted["vendor_name"] = m.group(1).strip()
                break
        if not extracted["vendor_name"] and lines:
            first_line = lines[0]
            if not re.search(r'invoice|tax|bill|receipt', first_line, re.IGNORECASE) and len(first_line) < 60:
                extracted["vendor_name"] = first_line

        # GSTIN
        gstin_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', invoice_text)
        if gstin_match:
            extracted["gstin"] = gstin_match.group(0)

        # Invoice Number
        inv_match = re.search(r'(?:Invoice\s*(?:No|#|Number|ID)|Bill\s*No|INV\s*#?)[:.\s]*([A-Za-z0-9\-_/]+)', invoice_text, re.IGNORECASE)
        if inv_match:
            extracted["invoice_number"] = inv_match.group(1).strip()
        else:
            inv_pattern = re.search(r'\b(INV-[A-Za-z0-9\-]+)\b', invoice_text, re.IGNORECASE)
            if inv_pattern:
                extracted["invoice_number"] = inv_pattern.group(1).strip()

        # Dates
        date_matches = re.findall(r'\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b', invoice_text)
        if date_matches:
            d_str = date_matches[0].replace('/', '-')
            parts = d_str.split('-')
            if len(parts[0]) == 4:
                extracted["invoice_date"] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            elif len(parts[2]) == 4:
                extracted["invoice_date"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

        # Amounts
        total_match = re.search(r'(?:Grand\s*Total|Total\s*Amount|Total|Net\s*Amount)\s*[:₹$]?\s*([0-9,]+\.?[0-9]{0,2})', invoice_text, re.IGNORECASE)
        if total_match:
            try:
                extracted["total_amount"] = float(total_match.group(1).replace(',', ''))
            except ValueError:
                pass

        subtotal_match = re.search(r'(?:Subtotal|Sub\s*Total)\s*[:₹$]?\s*([0-9,]+\.?[0-9]{0,2})', invoice_text, re.IGNORECASE)
        if subtotal_match:
            try:
                extracted["subtotal"] = float(subtotal_match.group(1).replace(',', ''))
            except ValueError:
                pass

        tax_match = re.search(r'(?:Tax|GST|VAT|CGST\s*\+\s*SGST)\s*(?:Amount)?\s*[:₹$]?\s*([0-9,]+\.?[0-9]{0,2})', invoice_text, re.IGNORECASE)
        if tax_match:
            try:
                extracted["tax_amount"] = float(tax_match.group(1).replace(',', ''))
            except ValueError:
                pass

        if extracted["total_amount"] and extracted["subtotal"] and not extracted["tax_amount"]:
            diff = extracted["total_amount"] - extracted["subtotal"]
            if diff > 0:
                extracted["tax_amount"] = round(diff, 2)

        return extracted

    # ------------------------------------------------------------------ #
    # Expense Categorizer
    # ------------------------------------------------------------------ #

    def categorize_expense(self, invoice_data: Dict[str, Any]) -> str:
        """Categorize expense based on invoice data keywords."""
        if not invoice_data.get("vendor_name") and not invoice_data.get("line_items"):
            return "Other"

        vendor_name = (invoice_data.get("vendor_name") or "").lower()
        item_descriptions = " ".join([
            item.get("description", "") for item in (invoice_data.get("line_items") or [])
        ]).lower()
        all_text = f"{vendor_name} {item_descriptions}"

        categories = {
            "Software & Technology": ["software", "saas", "subscription", "cloud", "api", "license", "microsoft", "google", "amazon", "azure", "aws"],
            "Travel": ["flight", "hotel", "travel", "taxi", "uber", "ola", "transport", "accommodation", "airfare"],
            "Marketing": ["marketing", "advertising", "promotion", "social media", "facebook", "google ads", "campaign"],
            "Office Supplies": ["office", "stationery", "furniture", "supplies", "paper", "printer", "toner"],
            "Utilities": ["electricity", "water", "internet", "phone", "utility", "gas", "broadband"],
            "Equipment": ["laptop", "computer", "hardware", "equipment", "machine", "device", "server"],
            "Logistics": ["shipping", "delivery", "courier", "freight", "transport", "logistics", "warehouse"],
            "Professional Services": ["consulting", "legal", "accounting", "audit", "professional", "services", "advisory"],
        }
        for category, keywords in categories.items():
            if any(kw in all_text for kw in keywords):
                return category
        return "Other"

    def close(self):
        """Close HTTP client."""
        self.client.close()


ai_service = AIService()
