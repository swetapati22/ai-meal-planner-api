"""
Meal Plan Generator (Per-Day LLM Generation)

Generates the entire day's meals in one LLM call:
- breakfast
- lunch
- dinner
- snack (only on even days)

Provides previous days' meals as context to ensure variety.
Includes per-meal fallback if LLM fails for individual meals.
"""
import uuid
import logging
import time
from datetime import datetime, timedelta

from app.models.schemas import MealPlanResponse, DayMealPlan, Meal
from app.services.llm_service import LLMService
from app.services.cache import CacheService
from app.core.config import settings

logger = logging.getLogger(__name__)


class MealPlanGenerator:

    def __init__(self):
        self.llm = LLMService()
        self.cache = CacheService()
        self.cache = CacheService()

    # ------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # ------------------------------------------------------------
    async def generate(self, params):
        total_start = time.time()

        logger.info("=" * 60)
        logger.info("[MEAL GEN] Starting full meal plan generation")
        logger.info(f"[MEAL GEN] Duration: {params.duration_days} days")
        logger.info("=" * 60)

        #Check cache first:
        dietary_restrictions = params.dietary_restrictions if hasattr(params, 'dietary_restrictions') else []
        preferences = params.preferences if hasattr(params, 'preferences') else []
        special_requirements = params.special_requirements if hasattr(params, 'special_requirements') else []
        
        cached_meal_plan = self.cache.get_meal_plan(
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
            duration_days=params.duration_days,
            special_requirements=special_requirements
        )
        
        if cached_meal_plan:
            logger.info("[CACHE] Returning cached meal plan")
            #Merge current query validation LLM logging with cached response:
            query_validation_llm_logging = params.llm_logging if hasattr(params, 'llm_logging') and params.llm_logging else None
            if query_validation_llm_logging:
                cached_meal_plan["query_validation_llm_logging"] = query_validation_llm_logging
            #Convert cached dict back to MealPlanResponse:
            return MealPlanResponse(**cached_meal_plan)

        #Cache miss - generate new meal plan:
        logger.info("[CACHE] Cache miss - generating new meal plan")

        meal_plan_id = str(uuid.uuid4())
        all_previous_meals = []    # This holds minimal context for variety across days
        day_plans = []
        
        #Track LLM usage for meal generation:
        meal_gen_llm_logging = {
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "tokens_total": 0,
            "llm_latency_ms": 0,
            "total_duration_ms": 0,
            "days_generated": 0,
            "per_day_logging": []
        }

        for day_index in range(1, params.duration_days + 1):
            date = (datetime.utcnow() + timedelta(days=day_index - 1)).strftime("%Y-%m-%d")

            logger.info("-" * 60)
            logger.info(f"[MEAL GEN] Day {day_index} ({date}) - generating daily meal plan")

            # Determine which meal types to generate today
            meal_types = ["breakfast", "lunch", "dinner"]
            if day_index % 2 == 0:
                meal_types.append("snack")  # Deterministic snack rule

            # Generate per-day meal set
            day_meals, day_llm_metrics = await self._generate_day_plan(
                day_index=day_index,
                date=date,
                params=params,
                meal_types=meal_types,
                prev_meals=all_previous_meals,  # pass minimal context for variety
            )
            
            #Aggregate LLM metrics:
            if day_llm_metrics:
                meal_gen_llm_logging["tokens_prompt"] += day_llm_metrics.get("tokens_prompt", 0)
                meal_gen_llm_logging["tokens_completion"] += day_llm_metrics.get("tokens_completion", 0)
                meal_gen_llm_logging["tokens_total"] += day_llm_metrics.get("tokens_total", 0)
                meal_gen_llm_logging["llm_latency_ms"] += day_llm_metrics.get("llm_latency_ms", 0)
                meal_gen_llm_logging["days_generated"] += 1
                meal_gen_llm_logging["per_day_logging"].append({
                    "day": day_index,
                    **day_llm_metrics
                })

            # Add today's meals to history for next-day variety and nutritional balance
            for m in day_meals.meals:
                all_previous_meals.append({
                    "meal_type": m.meal_type,
                    "recipe_name": m.recipe_name,
                    "description": m.description,
                    "nutritional_info": {
                        "calories": m.nutritional_info.calories,
                        "protein": m.nutritional_info.protein,
                        "carbs": m.nutritional_info.carbs,
                        "fat": m.nutritional_info.fat
                    }
                })

            day_plans.append(day_meals)

        summary = self._generate_summary(day_plans, params)

        elapsed = int((time.time() - total_start) * 1000)
        meal_gen_llm_logging["total_duration_ms"] = elapsed
        logger.info(f"[MEAL GEN] Finished generating {summary.total_meals} meals in {elapsed}ms")
        logger.info(f"[MEAL GEN] Total LLM tokens: {meal_gen_llm_logging['tokens_total']}, Total LLM latency: {meal_gen_llm_logging['llm_latency_ms']}ms")
        logger.info("=" * 60)
        logger.info("[MEAL GEN] Meal plan generation complete")
        logger.info("=" * 60)

        #Get query validation LLM logging from params:
        query_validation_llm_logging = params.llm_logging if hasattr(params, 'llm_logging') and params.llm_logging else None
        
        #Calculate total LLM logging (query validation + meal generation):
        total_llm_logging = None
        if query_validation_llm_logging or meal_gen_llm_logging.get("tokens_total", 0) > 0:
            query_tokens = query_validation_llm_logging.get("tokens_total", 0) if query_validation_llm_logging else 0
            meal_tokens = meal_gen_llm_logging.get("tokens_total", 0)
            query_time = query_validation_llm_logging.get("llm_latency_ms", 0) if query_validation_llm_logging else 0
            meal_time = meal_gen_llm_logging.get("llm_latency_ms", 0)
            
            total_llm_logging = {
                "tokens_prompt": (query_validation_llm_logging.get("tokens_prompt", 0) if query_validation_llm_logging else 0) + meal_gen_llm_logging.get("tokens_prompt", 0),
                "tokens_completion": (query_validation_llm_logging.get("tokens_completion", 0) if query_validation_llm_logging else 0) + meal_gen_llm_logging.get("tokens_completion", 0),
                "tokens_total": query_tokens + meal_tokens,
                "llm_latency_ms": query_time + meal_time,
                "total_duration_ms": elapsed,
                "query_validation_tokens": query_tokens,
                "meal_generation_tokens": meal_tokens,
                "query_validation_time_ms": query_time,
                "meal_generation_time_ms": meal_time
            }

        meal_plan_response = MealPlanResponse(
            meal_plan_id=meal_plan_id,
            duration_days=params.duration_days,
            generated_at=datetime.utcnow().isoformat() + "Z",
            meal_plan=day_plans,
            summary=summary,
            warnings=params.warnings if hasattr(params, 'warnings') else [],  # TODO: COMMENT OUT FOR SUBMISSION
            query_validation_llm_logging=query_validation_llm_logging,
            meal_generation_llm_logging=meal_gen_llm_logging if meal_gen_llm_logging.get("tokens_total", 0) > 0 else None,
            total_llm_logging=total_llm_logging
        )
        
        #Save to cache:
        try:
            #Convert Pydantic model to dict (works for both v1 and v2):
            if hasattr(meal_plan_response, 'model_dump'):
                meal_plan_dict = meal_plan_response.model_dump()  # Pydantic v2
            else:
                meal_plan_dict = meal_plan_response.dict()  # Pydantic v1
            
            self.cache.save_meal_plan(
                dietary_restrictions=dietary_restrictions,
                preferences=preferences,
                duration_days=params.duration_days,
                special_requirements=special_requirements,
                meal_plan_data=meal_plan_dict
            )
        except Exception as e:
            logger.warning(f"[CACHE] Failed to save meal plan to cache: {str(e)}")

        return meal_plan_response

    # ------------------------------------------------------------
    # ONE LLM CALL PER DAY
    # ------------------------------------------------------------
    async def _generate_day_plan(self, day_index, date, params, meal_types, prev_meals):
        """
        Calls the LLM ONCE to generate the full day's meal set.
        If a meal inside the day fails JSON/schema validation, fallback is used
        for THAT meal only.
        Returns: (DayMealPlan, day_llm_metrics)
        """
        day_llm_metrics = None
        try:
            llm_result = await self.llm.generate_day_plan(
                day_index=day_index,
                date=date,
                meal_types=meal_types,
                restrictions=params.dietary_restrictions,
                preferences=params.preferences,
                prev_meals=prev_meals
            )
            
            #Extract LLM metrics from response:
            day_llm_metrics = llm_result.pop("_llm_metrics", None)

            meals = []
            for meal_data in llm_result.get("meals", []):
                try:
                    #Normalize nutritional_info types (LLM may return ints, schema expects float for protein/carbs/fat):
                    if "nutritional_info" in meal_data:
                        ni = meal_data["nutritional_info"]
                        ni["protein"] = float(ni.get("protein", 20))
                        ni["carbs"] = float(ni.get("carbs", 40))
                        ni["fat"] = float(ni.get("fat", 10))
                        ni["calories"] = int(ni.get("calories", 350))
                    
                    #Ensure instructions is a string:
                    if "instructions" in meal_data and isinstance(meal_data["instructions"], list):
                        meal_data["instructions"] = " ".join(str(s) for s in meal_data["instructions"])
                    
                    meal_obj = Meal(**meal_data)
                    meals.append(meal_obj)
                except Exception as e:
                    logger.warning(f"[DAY GEN] Invalid meal JSON from LLM ({meal_data.get('meal_type')}), using LLM fallback. {str(e)[:50]}")
                    try:
                        fallback_meal_data = await self.llm.generate_single_meal(
                            meal_type=meal_data.get("meal_type", "lunch"),
                            restrictions=params.dietary_restrictions,
                            preferences=params.preferences,
                            special_requirements=params.special_requirements if hasattr(params, 'special_requirements') else [],
                            prev_meals=prev_meals
                        )
                        fallback_meal = Meal(**fallback_meal_data)
                        meals.append(fallback_meal)
                        logger.info(f"[FALLBACK] Successfully generated {meal_data.get('meal_type')} via LLM fallback")
                    except Exception as fallback_error:
                        logger.error(f"[FALLBACK] LLM fallback failed, using placeholder: {str(fallback_error)[:50]}")
                        placeholder = self._placeholder_recipe(meal_data.get("meal_type", "lunch"))
                        meals.append(placeholder)

            return (DayMealPlan(
                day=day_index,
                date=date,
                meals=meals
            ), day_llm_metrics)

        except Exception as e:
            logger.error(f"[DAY GEN] LLM day generation failed! Using LLM fallback for all meals. Error={str(e)[:100]}")
            fallback_meals = []
            fallback_metrics = {"tokens_prompt": 0, "tokens_completion": 0, "tokens_total": 0, "llm_latency_ms": 0}
            for mt in meal_types:
                try:
                    fallback_meal_data = await self.llm.generate_single_meal(
                        meal_type=mt,
                        restrictions=params.dietary_restrictions,
                        preferences=params.preferences,
                        special_requirements=params.special_requirements if hasattr(params, 'special_requirements') else [],
                        prev_meals=prev_meals
                    )
                    fallback_meal = Meal(**fallback_meal_data)
                    fallback_meals.append(fallback_meal)
                    logger.info(f"[FALLBACK] Successfully generated {mt} via LLM fallback")
                except Exception as fallback_error:
                    logger.error(f"[FALLBACK] LLM fallback failed for {mt}, using placeholder: {str(fallback_error)[:50]}")
                    placeholder = self._placeholder_recipe(mt)
                    fallback_meals.append(placeholder)
            return (DayMealPlan(day=day_index, date=date, meals=fallback_meals), fallback_metrics)

    # ------------------------------------------------------------
    # PLACEHOLDER (LAST RESORT)
    # ------------------------------------------------------------
    def _placeholder_recipe(self, meal_type):
        """Last resort placeholder recipe (only used if LLM fallback also fails)."""
        from app.models.schemas import NutritionalInfo

        return Meal(
            meal_type=meal_type,
            recipe_name=f"Simple {meal_type.title()} Bowl",
            description="A simple placeholder recipe.",
            ingredients=["ingredient 1", "ingredient 2"],
            nutritional_info=NutritionalInfo(
                calories=300,
                protein=12,
                carbs=40,
                fat=8
            ),
            preparation_time="15 mins",
            instructions="Mix ingredients and serve.",
            source="Placeholder"
        )

    # ------------------------------------------------------------
    # SUMMARY GENERATION
    # ------------------------------------------------------------
    def _generate_summary(self, day_plans, params):
        from app.models.schemas import MealPlanSummary
        import re

        total_meals = sum(len(day.meals) for day in day_plans)

        total_time = 0
        count = 0
        for day in day_plans:
            for meal in day.meals:
                match = re.search(r"(\d+)", meal.preparation_time)
                if match:
                    total_time += int(match.group(1))
                    count += 1

        avg_time = f"{total_time // count} mins" if count else "25 mins"

        base_cost = 2.0 if (hasattr(params, 'special_requirements') and params.special_requirements and "budget-friendly" in params.special_requirements) else 3.5

        min_cost = int(total_meals * base_cost)
        max_cost = int(total_meals * (base_cost + 1.5))

        return MealPlanSummary(
            total_meals=total_meals,
            dietary_compliance=params.dietary_restrictions + params.preferences,
            estimated_cost=f"${min_cost}-{max_cost}",
            avg_prep_time=avg_time
        )
