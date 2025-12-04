"""
LLM service for recipe generation
"""
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs"""
    
    def __init__(self):
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.provider = "openai"
        else:
            self.client = None
            self.provider = None
            logger.warning("No LLM API key configured")
    
    # ------------------------------------------------------------
    # DAY-LEVEL GENERATION (NEW - PRIMARY METHOD)
    # ------------------------------------------------------------
    async def generate_day_plan(
        self,
        day_index: int,
        date: str,
        meal_types: list,
        restrictions: list,
        preferences: list,
        prev_meals: list
    ) -> dict:
        """
        Generates all meals for a day in a single LLM call.
        Returns dict: { "meals": [ {...}, {...}, ... ] }
        """
        import time
        
        if not self.client:
            raise ValueError("LLM service not configured")
        
        prompt = self._build_day_prompt(
            day_index=day_index,
            date=date,
            meal_types=meal_types,
            restrictions=restrictions,
            preferences=preferences,
            prev_meals=prev_meals
        )
        
        llm_start_time = time.time()
        response = await self._call_llm(prompt)
        llm_latency_ms = int((time.time() - llm_start_time) * 1000)
        
        #Extract token usage:
        usage = response.usage
        tokens_prompt = usage.prompt_tokens if usage else 0
        tokens_completion = usage.completion_tokens if usage else 0
        tokens_total = usage.total_tokens if usage else 0
        
        logger.info(f"[LLM] Day {day_index} generation: {tokens_prompt}+{tokens_completion}={tokens_total} tokens, {llm_latency_ms}ms")
        
        raw = response.choices[0].message.content
        try:
            parsed_json = json.loads(raw)
            #Add LLM metrics to the response:
            parsed_json["_llm_metrics"] = {
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "tokens_total": tokens_total,
                "llm_latency_ms": llm_latency_ms
            }
            return parsed_json
        except Exception as e:
            logger.error(f"[DAY LLM] Invalid JSON: {raw[:200]}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    def _build_day_prompt(self, day_index, date, meal_types, restrictions, preferences, prev_meals):
        """Build the per-day prompt (HIGHLY DETERMINISTIC)"""
        from app.core.prompts import DAY_PLAN_PROMPT_TEMPLATE
        
        restrictions_text = ", ".join(restrictions) if restrictions else "none"
        preferences_text = ", ".join(preferences) if preferences else "none"
        
        #Minimal context from previous meals:
        prev_meals_text = "\n".join([
            f"- {m['meal_type']}: {m['recipe_name']} — {m['description']}"
            for m in prev_meals
        ]) or "None (Day 1)"
        
        #Calculate previous days' nutritional totals for balance:
        prev_nutrition_text = "None (Day 1)"
        if prev_meals:
            total_calories = sum(m.get('nutritional_info', {}).get('calories', 0) for m in prev_meals)
            total_protein = sum(m.get('nutritional_info', {}).get('protein', 0) for m in prev_meals)
            total_carbs = sum(m.get('nutritional_info', {}).get('carbs', 0) for m in prev_meals)
            total_fat = sum(m.get('nutritional_info', {}).get('fat', 0) for m in prev_meals)
            num_days = len(set(m.get('meal_type', '') for m in prev_meals)) // 3  # Approximate days
            if num_days == 0:
                num_days = 1
            
            prev_nutrition_text = f"""Previous {num_days} day(s) totals:
- Total Calories: {total_calories} ({total_calories // num_days if num_days > 0 else 0} avg/day)
- Total Protein: {total_protein:.1f}g ({total_protein / num_days if num_days > 0 else 0:.1f}g avg/day)
- Total Carbs: {total_carbs:.1f}g ({total_carbs / num_days if num_days > 0 else 0:.1f}g avg/day)
- Total Fat: {total_fat:.1f}g ({total_fat / num_days if num_days > 0 else 0:.1f}g avg/day)

Use this to ensure today's meals contribute to weekly nutritional balance."""
        
        meal_type_json = json.dumps(meal_types)
        
        return DAY_PLAN_PROMPT_TEMPLATE.format(
            day_index=day_index,
            date=date,
            meal_type_json=meal_type_json,
            restrictions_text=restrictions_text,
            preferences_text=preferences_text,
            prev_meals_text=prev_meals_text,
            prev_nutrition_text=prev_nutrition_text,
            meal_types=meal_types
        )
    
    async def _call_llm(self, prompt):
        """Internal LLM call (Stable & Strict JSON)"""
        if not self.client:
            raise ValueError("LLM service not configured")
        
        from app.core.prompts import DAY_PLAN_SYSTEM_PROMPT
        
        return await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": DAY_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
    
    # ------------------------------------------------------------
    # SINGLE MEAL FALLBACK GENERATION
    # ------------------------------------------------------------
    async def generate_single_meal(
        self,
        meal_type: str,
        restrictions: list,
        preferences: list,
        special_requirements: list = None,
        prev_meals: list = None
    ) -> dict:
        """
        Generate a single meal using LLM (used as fallback when day generation fails).
        Returns dict with single meal data.
        """
        import time
        
        if not self.client:
            raise ValueError("LLM service not configured")
        
        from app.core.prompts import SINGLE_MEAL_FALLBACK_PROMPT_TEMPLATE, SINGLE_MEAL_FALLBACK_SYSTEM_PROMPT
        
        restrictions_text = ", ".join(restrictions) if restrictions else "none"
        preferences_text = ", ".join(preferences) if preferences else "none"
        special_requirements_text = ", ".join(special_requirements) if special_requirements else "none"
        
        prev_meals_text = "\n".join([
            f"- {m.get('meal_type', 'unknown')}: {m.get('recipe_name', 'unknown')}"
            for m in (prev_meals or [])
        ]) or "None"
        
        prompt = SINGLE_MEAL_FALLBACK_PROMPT_TEMPLATE.format(
            meal_type=meal_type,
            restrictions_text=restrictions_text,
            preferences_text=preferences_text,
            special_requirements_text=special_requirements_text,
            prev_meals_text=prev_meals_text
        )
        
        try:
            llm_start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SINGLE_MEAL_FALLBACK_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                response_format={"type": "json_object"}
            )
            
            llm_latency_ms = int((time.time() - llm_start_time) * 1000)
            
            usage = response.usage
            tokens_prompt = usage.prompt_tokens if usage else 0
            tokens_completion = usage.completion_tokens if usage else 0
            tokens_total = usage.total_tokens if usage else 0
            
            logger.info(f"[LLM] Single meal fallback ({meal_type}): {tokens_prompt}+{tokens_completion}={tokens_total} tokens, {llm_latency_ms}ms")
            
            raw = response.choices[0].message.content
            meal_data = json.loads(raw)
            
            #Normalize types:
            if "nutritional_info" in meal_data:
                ni = meal_data["nutritional_info"]
                ni["protein"] = float(ni.get("protein", 20))
                ni["carbs"] = float(ni.get("carbs", 40))
                ni["fat"] = float(ni.get("fat", 10))
                ni["calories"] = int(ni.get("calories", 350))
            
            if "instructions" in meal_data and isinstance(meal_data["instructions"], list):
                meal_data["instructions"] = " ".join(str(s) for s in meal_data["instructions"])
            
            return meal_data
            
        except Exception as e:
            logger.error(f"[LLM] Single meal fallback failed for {meal_type}: {str(e)}")
            raise

