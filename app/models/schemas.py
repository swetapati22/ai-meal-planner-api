"""
Pydantic models for request/response validation
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class MealPlanRequest(BaseModel):
    """Request schema for meal plan generation"""
    query: str = Field(..., description="Natural language meal plan request", min_length=1)


class NutritionalInfo(BaseModel):
    """Nutritional information for a recipe"""
    calories: int = Field(..., ge=0, description="Calories per serving")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")


class Meal(BaseModel):
    """Individual meal/recipe"""
    meal_type: str = Field(..., description="Type of meal (breakfast, lunch, dinner, snack)")
    recipe_name: str = Field(..., description="Name of the recipe")
    description: str = Field(..., description="Description of the meal")
    ingredients: List[str] = Field(..., description="List of ingredients with quantities")
    nutritional_info: NutritionalInfo = Field(..., description="Nutritional information")
    preparation_time: str = Field(..., description="Estimated preparation time")
    instructions: str = Field(..., description="Step-by-step cooking instructions")
    source: str = Field(..., description="Source of the recipe (AI Generated, Recipe DB, URL)")


class DayMealPlan(BaseModel):
    """Meal plan for a single day"""
    day: int = Field(..., ge=1, description="Day number (1-indexed)")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    meals: List[Meal] = Field(..., description="List of meals for this day")


class MealPlanSummary(BaseModel):
    """Summary statistics for the meal plan"""
    total_meals: int = Field(..., ge=0, description="Total number of meals")
    dietary_compliance: List[str] = Field(..., description="List of dietary restrictions/preferences followed")
    estimated_cost: Optional[str] = Field(None, description="Estimated cost range")
    avg_prep_time: Optional[str] = Field(None, description="Average preparation time")


class MealPlanResponse(BaseModel):
    """Response schema for meal plan generation"""
    meal_plan_id: str = Field(..., description="Unique identifier for the meal plan")
    duration_days: int = Field(..., ge=1, le=7, description="Number of days in the meal plan")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    meal_plan: List[DayMealPlan] = Field(..., description="List of daily meal plans")
    summary: MealPlanSummary = Field(..., description="Summary statistics")
    
    # ============================================================================
    # TODO: COMMENT OUT FOR SUBMISSION - Testing only
    # NOTE: Warnings field - schema change not explicitly requested in assignment
    # If UI team can accommodate schema changes, this can be kept to display warnings as tooltips
    # Example UI tooltip: "You requested >7 days of meal plan. Here is a 7-day meal plan. 
    #                     You can rotate the meals for the next week or come back with feedback 
    #                     and we would be happy to generate more."
    # ============================================================================
    warnings: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Warnings about adjustments made to the request. Format: [{'category': 'days_capped_at_7', 'value': 'warning message'}]"
    )
    
    # ============================================================================
    # LLM Performance Tracking
    # ============================================================================
    query_validation_llm_logging: Optional[Dict] = Field(
        default=None,
        description="LLM logging for query validation phase (tokens, latency, changes made)"
    )
    meal_generation_llm_logging: Optional[Dict] = Field(
        default=None,
        description="LLM logging for meal generation phase (aggregated across all days)"
    )
    total_llm_logging: Optional[Dict] = Field(
        default=None,
        description="Total LLM usage across all phases (combined tokens and time)"
    )
    # ============================================================================

