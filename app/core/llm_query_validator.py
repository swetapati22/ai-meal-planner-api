"""
LLM-based query validation and enhancement
Validates and enhances regex-extracted query parameters using LLM
"""
import json
import time
import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.prompts import QUERY_VALIDATION_SYSTEM_PROMPT
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class LLMQueryValidator:
    """Validate and enhance extracted query parameters using LLM"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.enabled = settings.openai_api_key is not None
    
    async def validate_and_enhance(
        self,
        user_query: str,
        initial_extraction: Dict,
        known_dietary_restrictions: List[str] = None,
        known_preferences: List[str] = None,
        known_special_requirements: List[str] = None
    ) -> Dict:
        """
        Validate and enhance extracted parameters using LLM
        Returns:
            {
                "validated": {...},
                "additional_warnings": [...],
                "llm_logging": {...}
            }
        """
        if not self.enabled:
            logger.info("LLM validation skipped: No API key configured")
            return {
                "validated": initial_extraction,
                "additional_warnings": [],
                "llm_logging": {
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "tokens_total": 0,
                    "llm_latency_ms": 0,
                    "enabled": False
                }
            }
        
        start_time = time.time()
        
        #Build prompt:
        prompt = self._build_validation_prompt(
            user_query,
            initial_extraction,
            known_dietary_restrictions or [],
            known_preferences or [],
            known_special_requirements or []
        )
        
        #Call LLM with structured output:
        try:
            response_obj = await self._call_llm_with_schema(prompt)
            llm_latency_ms = int((time.time() - start_time) * 1000)
            
            #Parse response content:
            content = response_obj.choices[0].message.content
            result = json.loads(content)
            
            #Extract validated results:
            validated = result.get("validated", initial_extraction)
            
            #Track changes made by LLM:
            changes = self._detect_changes(initial_extraction, validated)
            
            #Log additional warnings:
            additional_warnings = result.get("additional_warnings", [])
            
            #Extract token usage from OpenAI response:
            usage = response_obj.usage
            tokens_prompt = usage.prompt_tokens if usage else 0
            tokens_completion = usage.completion_tokens if usage else 0
            tokens_total = usage.total_tokens if usage else 0
            
            llm_logging = {
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "tokens_total": tokens_total,
                "llm_latency_ms": llm_latency_ms,
                "enabled": True,
                "changes_made": changes  #Track what changed
            }
            
            return {
                "validated": validated,
                "additional_warnings": additional_warnings,
                "llm_logging": llm_logging
            }
            
        except Exception as e:
            logger.error(f"[LLM] Validation failed: {str(e)}")
            llm_latency_ms = int((time.time() - start_time) * 1000)
            return {
                "validated": initial_extraction,
                "additional_warnings": [],
                "llm_logging": {
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "tokens_total": 0,
                    "llm_latency_ms": llm_latency_ms,
                    "enabled": True,
                    "error": str(e)
                }
            }
    
    def _build_validation_prompt(
        self,
        user_query: str,
        initial_extraction: Dict,
        known_dietary_restrictions: List[str],
        known_preferences: List[str],
        known_special_requirements: List[str]
    ) -> str:
        """Build the validation prompt for LLM"""
        from app.core.prompts import QUERY_VALIDATION_PROMPT_TEMPLATE
        
        return QUERY_VALIDATION_PROMPT_TEMPLATE.format(
            user_query=user_query,
            initial_extraction=json.dumps(initial_extraction, indent=2),
            known_dietary_restrictions=', '.join(known_dietary_restrictions),
            known_preferences=', '.join(known_preferences),
            known_special_requirements=', '.join(known_special_requirements)
        )
    
    async def _call_llm_with_schema(self, prompt: str):
        """Call LLM with JSON schema constraint"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        #Define JSON schema for response:
        json_schema = {
            "type": "object",
            "properties": {
                "validated": {
                    "type": "object",
                    "properties": {
                        "duration_days": {"type": "integer", "minimum": 1, "maximum": 7},
                        "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                        "preferences": {"type": "array", "items": {"type": "string"}},
                        "special_requirements": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["duration_days", "dietary_restrictions", "preferences", "special_requirements"]
                },
                "additional_warnings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["category", "value"]
                    }
                }
            },
            "required": ["validated", "additional_warnings"]
        }
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": QUERY_VALIDATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_schema", "json_schema": {"name": "query_validation", "schema": json_schema}},
            temperature=0.3  #Lower temperature for more consistent validation
        )
        
        return response
    
    def _detect_changes(self, initial: Dict, validated: Dict) -> Dict:
        """Detect what changes LLM made compared to regex extraction"""
        changes = {}
        
        #Compare duration:
        if initial.get("duration_days") != validated.get("duration_days"):
            changes["duration_days"] = {
                "from": initial.get("duration_days"),
                "to": validated.get("duration_days")
            }
        
        #Compare dietary restrictions:
        initial_restrictions = set(initial.get("dietary_restrictions", []))
        validated_restrictions = set(validated.get("dietary_restrictions", []))
        if initial_restrictions != validated_restrictions:
            added = list(validated_restrictions - initial_restrictions)
            removed = list(initial_restrictions - validated_restrictions)
            if added or removed:
                changes["dietary_restrictions"] = {
                    "added": added,
                    "removed": removed
                }
        
        #Compare preferences:
        initial_preferences = set(initial.get("preferences", []))
        validated_preferences = set(validated.get("preferences", []))
        if initial_preferences != validated_preferences:
            added = list(validated_preferences - initial_preferences)
            removed = list(initial_preferences - validated_preferences)
            if added or removed:
                changes["preferences"] = {
                    "added": added,
                    "removed": removed
                }
        
        #Compare special requirements:
        initial_special = set(initial.get("special_requirements", []))
        validated_special = set(validated.get("special_requirements", []))
        if initial_special != validated_special:
            added = list(validated_special - initial_special)
            removed = list(initial_special - validated_special)
            if added or removed:
                changes["special_requirements"] = {
                    "added": added,
                    "removed": removed
                }
        
        return changes

