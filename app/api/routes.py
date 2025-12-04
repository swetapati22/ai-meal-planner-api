"""
API routes for the meal planner (AI Meal Planner API) 
"""
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import MealPlanRequest, MealPlanResponse
from app.core.meal_generator import MealPlanGenerator
from app.core.query_parser import QueryParser
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["meal-planner"])

@router.post(
    "/generate-meal-plan",
    response_model=MealPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a personalized meal plan",
    description="Generate a custom-day meal plan based on natural language query"
)
async def generate_meal_plan(request: MealPlanRequest):
    """
    Generate a personalized meal plan from a natural language query.
    The request body must match MealPlanRequest schema.
    Args: 
        request: MealPlanRequest containing the natural language query
        Returns: MealPlanResponse with the generated meal plan
        Raises: HTTPException: If meal plan generation fails
    """
    try:
        #Parse the query:
        query_parser = QueryParser()
        #Calling the query parser to extract the parameters from the natural language query: Create a 5-day meal plan, 1800 calories/day, gluten-free
        #The parser turns it into structured parameters:
        #{
        #   "days": 5,
        #   "calories_per_day": 1800,
        #   "dietary_restrictions": ["gluten-free"]
        # }
        parsed_params = await query_parser.parse(request.query)
        
        #Generate meal plan:
        meal_generator = MealPlanGenerator()
        #This class handles:
            #Recipe sourcing
            #Filtering by calories
            #Dietary restrictions
            #Number of meals per day
            #AI-based generation
        #It returns a structured meal plan that matches the MealPlanResponse schema.
        meal_plan = await meal_generator.generate(parsed_params)
        return meal_plan
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, #User/client made a mistake
            detail=f"Invalid request: {str(e)}"
        )
    #The QueryParser might detect invalid input
    #The MealPlanGenerator might find missing or invalid parameters
    #Request body is not usable (even though Pydantic validated structure)
    except Exception as e:
        logger.error(f"Error generating meal plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, #server made a mistake
            detail="Failed to generate meal plan. Please try again."
        )
        #Anything at all that is not a ValueError, including:
            #Bugs in code
            #API provider failures
            #Recipe sources failing
            #Unexpected data shape
            #Network issues
            #AI model errors
            #JSON parsing issues
            #ZeroDivisionError, TypeError, KeyError, etc.

@router.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "meal-planner-api"}

