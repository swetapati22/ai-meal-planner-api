"""
Natural language query parsing and intent extraction
"""
import re
import logging
import time
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from app.core.config import settings
from app.core.llm_query_validator import LLMQueryValidator

logger = logging.getLogger(__name__)

@dataclass
class ParsedQueryParams:
    """Structured parameters extracted from user query"""
    duration_days: int = 7  # Default to 7 days
    dietary_restrictions: List[str] = None
    preferences: List[str] = None
    special_requirements: List[str] = None
    warnings: List[str] = None  #Warnings about adjustments made, predefined categories: days_capped_at_7, dietary_restrictions_conflict, preferences_conflict, special_requirements_conflict for the easy of usability by the UI/UX developer:
    llm_logging: Dict = None  #LLM validation logging (tokens, latency, etc.)
    
    def __post_init__(self): #Runs after the object is created and after __init__ is called:
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.preferences is None:
            self.preferences = []
        if self.special_requirements is None:
            self.special_requirements = []
        if self.warnings is None:
            self.warnings = []
        if self.llm_logging is None:
            self.llm_logging = {}

class QueryParser:
    """Parse natural language queries to extract meal plan parameters"""
    #Common dietary restrictions:
    DIETARY_RESTRICTIONS = {
        'vegan', 'vegetarian', 'pescatarian', 'paleo', 'keto',
        'gluten-free', 'dairy-free', 'nut-free', 'soy-free',
        'halal', 'kosher', 'mediterranean', 'dash'
    }
    
    #Common preferences (nutritional goals):
    PREFERENCES = {
        'low-carb', 'high-protein', 'low-fat', 'low-sodium'
    }
    
    #Duration patterns:
    DURATION_PATTERNS = [
        (r'(\d+)[\s-]*day', 1),  #"5 day", "3-day", "3 day" (matches space or hyphen)
        (r'(\d+)\s*week', 7),  #"1 week" = 7 days
        (r'week', 7),  #"week" = 7 days
    ]
    
    #Main Parse Method:
    async def parse(self, query: str) -> ParsedQueryParams:
        """
        Parse natural language query and extract parameters.
        Args: query: Natural language query string
        Returns: ParsedQueryParams with extracted information
        """
        total_start_time = time.time()
        regex_start_time = time.time()
        query_lower = query.lower()
        warnings = []

        ######################### Extract duration: #########################        
        logger.info("=" * 60)
        logger.info("[REGEX] Starting query parsing...")
        logger.info("=" * 60)
        
        duration, was_explicitly_specified = self._extract_duration(query_lower)
        
        #Warn if duration was not specified (defaulted to 7 days):
        if not was_explicitly_specified:
            warning_message = "Duration not specified. Defaulting to 7 days."
            warning_obj = {
                "category": "days_unspecified",
                "value": warning_message
            }
            warnings.append(warning_obj)
            logger.warning(f"[REGEX] Duration unspecified → defaulting to 7 days")
        
        #Cap duration to 7 days maximum:
        if duration > 7:
            warning_message = f"Requested {duration} days. Limited to 7 days maximum."
            warning_obj = {
                "category": "days_capped_at_7",
                "value": warning_message
            }
            warnings.append(warning_obj)
            logger.warning(f"[REGEX] Duration capped: {duration} → 7 days")
            duration = 7
        
        ######################### Extract dietary restrictions: ######################### 
        dietary_restrictions = self._extract_dietary_restrictions(query_lower)
        
        #Warn if dietary restrictions were not specified:
        if not dietary_restrictions:
            warning_message = "No dietary restrictions specified. Generating general meal plan."
            warning_obj = {
                "category": "dietary_restrictions_unspecified",
                "value": warning_message
            }
            warnings.append(warning_obj)
            logger.warning(f"[REGEX] No dietary restrictions found")
        
        ######################### Extract preferences: ######################### 
        preferences = self._extract_preferences(query_lower)
        
        #Warn if preferences were not specified:
        if not preferences:
            warning_message = "No nutritional preferences specified. Generating balanced meal plan."
            warning_obj = {
                "category": "preferences_unspecified",
                "value": warning_message
            }
            warnings.append(warning_obj)
            logger.warning(f"[REGEX] No preferences found")
        
        ######################### Extract special requirements: ######################### 
        special_requirements = self._extract_special_requirements(query_lower)
        
        #Warn if special requirements were not specified:
        if not special_requirements:
            warning_message = "No special requirements specified. Generating standard meal plan."
            warning_obj = {
                "category": "special_requirements_unspecified",
                "value": warning_message
            }
            warnings.append(warning_obj)
            logger.warning(f"[REGEX] No special requirements found")
        
        ######################### Validate for conflicts: ######################### 
        conflict_warnings = self._validate_restrictions(dietary_restrictions)
        warnings.extend(conflict_warnings)
        
        #Calculate regex matching time:
        regex_latency_ms = int((time.time() - regex_start_time) * 1000)
        logger.info(f"[REGEX] Completed in {regex_latency_ms}ms")
        logger.info(f"[REGEX] Extracted: {duration} days, restrictions: {dietary_restrictions}, preferences: {preferences}, special: {special_requirements}")
        
        #Initial extraction result (before LLM validation) - with warnings for logging:
        initial_extraction_with_warnings = {
            "duration_days": duration,
            "dietary_restrictions": dietary_restrictions,
            "preferences": preferences,
            "special_requirements": special_requirements,
            "warnings": warnings
        }
        
        #Initial extraction WITHOUT warnings to pass to LLM (LLM will add its own warnings):
        initial_extraction_for_llm = {
            "duration_days": duration,
            "dietary_restrictions": dietary_restrictions,
            "preferences": preferences,
            "special_requirements": special_requirements
        }
        
        ######################### LLM Validation and Enhancement: ######################### 
        llm_logging = {
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "tokens_total": 0,
            "llm_latency_ms": 0,
            "regex_latency_ms": regex_latency_ms,
            "total_duration_ms": 0,
            "enabled": False
        }
        
        final_duration = duration
        final_dietary_restrictions = dietary_restrictions
        final_preferences = preferences
        final_special_requirements = special_requirements
        final_warnings = warnings.copy()  #Start with regex warnings
        
        if settings.enable_llm_validation:
            logger.info("=" * 60)
            logger.info("[LLM] Starting validation...")
            logger.info("=" * 60)
            try:
                validator = LLMQueryValidator()
                llm_result = await validator.validate_and_enhance(
                    user_query=query,
                    initial_extraction=initial_extraction_for_llm,  #Pass without warnings - LLM should not see regex warnings
                    known_dietary_restrictions=list(self.DIETARY_RESTRICTIONS),
                    known_preferences=list(self.PREFERENCES),
                    known_special_requirements=['budget-friendly', 'quick', 'easy', 'healthy']
                )
                
                #Merge LLM validated results - ONLY accept additions or corrections, never removals:
                validated = llm_result.get("validated", {})
                
                #Duration: only update if LLM corrected an invalid value (>7 or <1):
                validated_duration = validated.get("duration_days", duration)
                if validated_duration != duration:
                    if duration > 7 or duration < 1:
                        final_duration = validated_duration
                        logger.info(f"[LLM] Corrected duration: {duration} → {validated_duration}")
                    else:
                        logger.info(f"[LLM] Preserving regex duration: {duration}")
                
                #Dietary restrictions, preferences, special_requirements: only ADD new items found by LLM:
                validated_restrictions = set(validated.get("dietary_restrictions", dietary_restrictions))
                validated_prefs = set(validated.get("preferences", preferences))
                validated_special = set(validated.get("special_requirements", special_requirements))
                
                #Only add items that LLM found but regex missed (preserve all regex findings):
                added_restrictions = validated_restrictions - set(dietary_restrictions)
                if added_restrictions:
                    final_dietary_restrictions = list(set(dietary_restrictions) | added_restrictions)
                    logger.info(f"[LLM] Added restrictions: {added_restrictions}")
                
                added_prefs = validated_prefs - set(preferences)
                if added_prefs:
                    final_preferences = list(set(preferences) | added_prefs)
                    logger.info(f"[LLM] Added preferences: {added_prefs}")
                
                added_special = validated_special - set(special_requirements)
                if added_special:
                    final_special_requirements = list(set(special_requirements) | added_special)
                    logger.info(f"[LLM] Added special reqs: {added_special}")
                
                #Log LLM changes for traceability:
                llm_changes = llm_result.get("llm_logging", {}).get("changes_made", {})
                if llm_changes:
                    logger.info(f"[LLM] Changes detected: {list(llm_changes.keys())}")
                else:
                    logger.info(f"[LLM] No changes - regex extraction accurate")
                
                #Add LLM additional warnings (deduplicate against initial warnings):
                additional_warnings = llm_result.get("additional_warnings", [])
                if additional_warnings:
                    #Get initial warning categories to avoid duplicates:
                    initial_categories = {w.get('category') for w in warnings}
                    #Only add warnings that don't already exist in initial warnings:
                    new_warnings = [w for w in additional_warnings if w.get('category') not in initial_categories]
                    if new_warnings:
                        final_warnings.extend(new_warnings)
                        logger.info(f"[LLM] Added {len(new_warnings)} new warning(s)")
                    else:
                        logger.info(f"[LLM] Skipped {len(additional_warnings)} duplicate warning(s)")
                
                #Update LLM logging:
                llm_logging = llm_result.get("llm_logging", {})
                llm_logging["regex_latency_ms"] = regex_latency_ms
                logger.info(f"[LLM] Completed in {llm_logging.get('llm_latency_ms', 0)}ms")
                
            except Exception as e:
                logger.error(f"[LLM] Validation error: {str(e)}")
                llm_logging["error"] = str(e)
        
        #Calculate total duration:
        total_duration_ms = int((time.time() - total_start_time) * 1000)
        llm_logging["total_duration_ms"] = total_duration_ms
        
        #Data dump (if enabled):
        if settings.enable_query_dump:
            self._dump_query_data(query, initial_extraction_with_warnings, {
                "duration_days": final_duration,
                "dietary_restrictions": final_dietary_restrictions,
                "preferences": final_preferences,
                "special_requirements": final_special_requirements,
                "warnings": final_warnings
            }, llm_logging)
        
        return ParsedQueryParams(
            duration_days=final_duration,
            dietary_restrictions=final_dietary_restrictions,
            preferences=final_preferences,
            special_requirements=final_special_requirements,
            warnings=final_warnings,
            llm_logging=llm_logging
        )

    ######################### Extract duration: #########################        
    def _extract_duration(self, query: str) -> Tuple[int, bool]:
        """
        Extract number of days from query
        Returns: (duration, was_explicitly_specified)
        """
        #Try to find explicit number:
        for pattern, multiplier in self.DURATION_PATTERNS:
            match = re.search(pattern, query)
            if match:
                if multiplier == 1:
                    return (int(match.group(1)), True)  #Explicitly specified by the user:
                else:
                    #For "week" patterns:
                    if match.groups():
                        return (int(match.group(1)) * multiplier, True)  #Explicitly specified by the user:
                    return (multiplier, True)  #"week" is explicitly specified by the user:
        
        #Try to extract from phrases like "next week", "this week", "for the week":
        if re.search(r'\b(next|this|for the|for a)\s+week\b', query, re.IGNORECASE):
            return (7, True)
        
        #Try to extract from phrases like "for 5 days", "over 3 days"
        day_match = re.search(r'\b(for|over)\s+(\d+)\s+days?\b', query, re.IGNORECASE)
        if day_match:
            return (int(day_match.group(2)), True)  #Explicitly specified by the user:
        
        #Default to 7 days if not specified:
        return (7, False)  #Not explicitly specified by the user:

    ######################### Extract Dietary Restrictions: ######################### 
    def _extract_dietary_restrictions(self, query: str) -> List[str]:
        """Extract dietary restrictions from query"""
        found = []
        for restriction in self.DIETARY_RESTRICTIONS:
            # Check for exact match or with hyphen
            pattern = rf'\b{re.escape(restriction.replace("-", "[- ]"))}\b'
            if re.search(pattern, query, re.IGNORECASE):
                found.append(restriction)
        return found

    ######################### Extract Preferences: ######################### 
    def _extract_preferences(self, query: str) -> List[str]:
        """Extract preferences from query"""
        found = []
        for preference in self.PREFERENCES:
            pattern = rf'\b{re.escape(preference.replace("-", "[- ]"))}\b'
            if re.search(pattern, query, re.IGNORECASE):
                found.append(preference)
        return found

    ######################### Extract Special Requirements: ######################### 
    def _extract_special_requirements(self, query: str) -> List[str]:
        """Extract special requirements (budget-friendly, quick, healthy, etc.)"""
        special = []
        
        #Budget-friendly:
        if re.search(r'\b(budget|cheap|affordable|inexpensive|low.?cost)\b', query, re.IGNORECASE):
            special.append('budget-friendly')
        
        #Quick/Fast:
        if re.search(r'\b(quick|fast|15\s*min|under\s*\d+\s*min|quickly|rapid)\b', query, re.IGNORECASE):
            special.append('quick')
        
        #Easy/Simple:
        if re.search(r'\b(easy|simple|simple|straightforward)\b', query, re.IGNORECASE):
            special.append('easy')
        
        #Healthy:
        if re.search(r'\b(healthy|nutritious|wholesome)\b', query, re.IGNORECASE):
            special.append('healthy')
        
        return special

    ######################### Validate for conflicts: ######################### 
    def _validate_restrictions(self, restrictions: List[str]) -> List[dict]:
        """
        Validate that restrictions don't conflict
        Returns: List of warning objects for conflicts (errors are still raised)
        Note: We do NOT silently remove restrictions - all conflicts raise errors for user to resolve
        """
        conflict_warnings = []
        # Check for conflicting restrictions - all conflicts raise errors, no silent removal
        conflicts = [
            (['vegan', 'pescatarian'], 'Vegan and pescatarian are conflicting - vegan excludes all animal products including fish'),
            (['vegan', 'vegetarian'], 'Vegan and vegetarian are conflicting - please choose one. Vegan excludes all animal products, vegetarian excludes meat but allows dairy/eggs'),
            (['pescatarian', 'vegetarian'], 'Pescatarian and vegetarian are conflicting - pescatarian includes fish, vegetarian does not. Please choose one'),
        ]
        
        restriction_set = set(restrictions)
        for conflict_pair, message in conflicts:
            if all(r in restriction_set for r in conflict_pair):
                #Add warning before raising error:
                warning_message = f"Conflicting dietary restrictions detected: {', '.join(conflict_pair)}. {message}"
                warning_obj = {
                    "category": "conflicting_restrictions",
                    "value": warning_message
                }
                conflict_warnings.append(warning_obj)
                #Log warning for monitoring:
                logger.warning(f"[REGEX] Conflict detected: {', '.join(conflict_pair)}")
                raise ValueError(message)
        
        return conflict_warnings

    ######################### Data Dump: ######################### 
    def _dump_query_data(self, query: str, initial_extraction: Dict, final_extraction: Dict, llm_logging: Dict):
        """Save query parsing data to file for debugging"""
        dump_dir = "query_dumps"
        os.makedirs(dump_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"{dump_dir}/query_dump_{timestamp}.json"
        
        dump_data = {
            "timestamp": timestamp,
            "query": query,
            "initial_extraction": initial_extraction,
            "final_extraction": final_extraction,
            "llm_logging": llm_logging
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(dump_data, f, indent=2)
            logger.info(f"Query data dumped to {filename}")
        except Exception as e:
            logger.error(f"Failed to dump query data: {str(e)}")

