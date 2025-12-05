# API Documentation

## Base URL

```
http://localhost:8001
```

## Interactive Documentation

- **Swagger UI**: `http://localhost:8001/docs`

---

## Endpoints

### 1. Generate Meal Plan

**Endpoint:** `POST /api/generate-meal-plan`

**Description:** Generates a personalized, multi-day meal plan based on a natural language query.

**Request Body:**
```json
{
  "query": "string - Natural language meal plan request"
}
```

**Request Schema:**
- `query` (string, required): Natural language query describing the desired meal plan
  - Minimum length: 1 character
  - Examples:
    - "Create a 5-day vegetarian meal plan with high protein"
    - "I need a 3-day gluten-free meal plan, exclude dairy and nuts"
    - "Generate a week of low-carb meals for two people, budget-friendly"
    - "7-day Mediterranean diet plan with quick breakfast options"

**Response Schema:**
```json
{
  "meal_plan_id": "string (UUID)",
  "duration_days": "integer (1-7)",
  "generated_at": "string (ISO timestamp)",
  "meal_plan": [
    {
      "day": "integer (1-indexed)",
      "date": "string (YYYY-MM-DD)",
      "meals": [
        {
          "meal_type": "string (breakfast|lunch|dinner|snack)",
          "recipe_name": "string",
          "description": "string",
          "ingredients": ["string"],
          "nutritional_info": {
            "calories": "integer",
            "protein": "float (grams)",
            "carbs": "float (grams)",
            "fat": "float (grams)"
          },
          "preparation_time": "string",
          "instructions": "string",
          "source": "string"
        }
      ]
    }
  ],
  "summary": {
    "total_meals": "integer",
    "dietary_compliance": ["string"],
    "estimated_cost": "string",
    "avg_prep_time": "string"
  },
  "warnings": [
    {
      "category": "string",
      "value": "string"
    }
  ],
  "query_validation_llm_logging": {
    "tokens_prompt": "integer",
    "tokens_completion": "integer",
    "tokens_total": "integer",
    "llm_latency_ms": "integer",
    "regex_latency_ms": "integer",
    "total_duration_ms": "integer",
    "enabled": "boolean",
    "changes_made": {}
  },
  "meal_generation_llm_logging": {
    "tokens_prompt": "integer",
    "tokens_completion": "integer",
    "tokens_total": "integer",
    "llm_latency_ms": "integer",
    "total_duration_ms": "integer",
    "days_generated": "integer",
    "per_day_logging": [
      {
        "day": "integer",
        "tokens_prompt": "integer",
        "tokens_completion": "integer",
        "tokens_total": "integer",
        "llm_latency_ms": "integer"
      }
    ]
  },
  "total_llm_logging": {
    "tokens_prompt": "integer",
    "tokens_completion": "integer",
    "tokens_total": "integer",
    "llm_latency_ms": "integer",
    "total_duration_ms": "integer",
    "query_validation_tokens": "integer",
    "meal_generation_tokens": "integer",
    "query_validation_time_ms": "integer",
    "meal_generation_time_ms": "integer"
  }
}
```

**Response Codes:**
- `200 OK`: Meal plan generated successfully
- `400 Bad Request`: Invalid query or parameters
- `422 Unprocessable Entity`: Request validation error
- `500 Internal Server Error`: Server error during generation

**Example Request:**
```bash
curl -X POST "http://localhost:8001/api/generate-meal-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a 5-day vegetarian meal plan with high protein"
  }'
```

**Example Response:**
```json
{
  "meal_plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_days": 5,
  "generated_at": "2025-01-15T10:30:00Z",
  "meal_plan": [
    {
      "day": 1,
      "date": "2025-01-15",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "High-Protein Oatmeal Bowl",
          "description": "A nutritious breakfast with Greek yogurt and berries",
          "ingredients": [
            "1 cup rolled oats",
            "1 cup Greek yogurt",
            "1/2 cup mixed berries",
            "2 tbsp chia seeds"
          ],
          "nutritional_info": {
            "calories": 350,
            "protein": 25.0,
            "carbs": 45.0,
            "fat": 8.0
          },
          "preparation_time": "15 mins",
          "instructions": "Cook oats according to package. Mix in Greek yogurt and top with berries and chia seeds.",
          "source": "AI Generated"
        },
        {
          "meal_type": "lunch",
          "recipe_name": "Quinoa and Black Bean Bowl",
          "description": "Protein-rich vegetarian lunch",
          "ingredients": [
            "1 cup cooked quinoa",
            "1/2 cup black beans",
            "1/2 cup corn",
            "1/4 cup avocado"
          ],
          "nutritional_info": {
            "calories": 420,
            "protein": 18.0,
            "carbs": 55.0,
            "fat": 12.0
          },
          "preparation_time": "20 mins",
          "instructions": "Combine cooked quinoa with black beans and corn. Top with sliced avocado.",
          "source": "AI Generated"
        },
        {
          "meal_type": "dinner",
          "recipe_name": "Lentil Curry",
          "description": "Hearty vegetarian dinner",
          "ingredients": [
            "1 cup red lentils",
            "1 can coconut milk",
            "1 onion",
            "2 cloves garlic"
          ],
          "nutritional_info": {
            "calories": 480,
            "protein": 22.0,
            "carbs": 60.0,
            "fat": 15.0
          },
          "preparation_time": "30 mins",
          "instructions": "Sauté onions and garlic. Add lentils and coconut milk. Simmer until lentils are tender.",
          "source": "AI Generated"
        }
      ]
    }
  ],
  "summary": {
    "total_meals": 15,
    "dietary_compliance": ["vegetarian", "high-protein"],
    "estimated_cost": "$45-60",
    "avg_prep_time": "25 mins"
  },
  "warnings": [],
  "query_validation_llm_logging": {
    "tokens_prompt": 500,
    "tokens_completion": 300,
    "tokens_total": 800,
    "llm_latency_ms": 2560,
    "regex_latency_ms": 0,
    "total_duration_ms": 2560,
    "enabled": true,
    "changes_made": {}
  },
  "meal_generation_llm_logging": {
    "tokens_prompt": 2277,
    "tokens_completion": 2287,
    "tokens_total": 4564,
    "llm_latency_ms": 49180,
    "total_duration_ms": 49184,
    "days_generated": 5,
    "per_day_logging": [
      {
        "day": 1,
        "tokens_prompt": 595,
        "tokens_completion": 684,
        "tokens_total": 1279,
        "llm_latency_ms": 16301
      }
    ]
  },
  "total_llm_logging": {
    "tokens_prompt": 2777,
    "tokens_completion": 2587,
    "tokens_total": 5364,
    "llm_latency_ms": 51740,
    "total_duration_ms": 49184,
    "query_validation_tokens": 800,
    "meal_generation_tokens": 4564,
    "query_validation_time_ms": 2560,
    "meal_generation_time_ms": 49180
  }
}
```

---

### 2. Health Check

**Endpoint:** `GET /api/health`

**Description:** Returns the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "service": "meal-planner-api"
}
```

**Response Codes:**
- `200 OK`: Service is healthy

**Example Request:**
```bash
curl -X GET "http://localhost:8001/api/health"
```

---

## Query Examples

### Basic Queries

1. **Simple duration and diet:**
   ```
   "Create a 3-day vegetarian meal plan"
   ```

2. **With preferences:**
   ```
   "Generate a 5-day low-carb meal plan"
   ```

3. **Multiple restrictions:**
   ```
   "I need a 7-day gluten-free, dairy-free meal plan"
   ```

### Complex Queries

1. **Multiple requirements:**
   ```
   "Generate a 7-day low-carb, dairy-free meal plan with high protein, budget-friendly options"
   ```

2. **With time constraints:**
   ```
   "I need a week of quick breakfast recipes under 15 minutes"
   ```

3. **Lifestyle requirements:**
   ```
   "Create a 5-day Mediterranean diet plan with easy recipes"
   ```

### Edge Cases

1. **Ambiguous query:**
   ```
   "I need healthy meals for next week"
   ```
   - Defaults to 7 days
   - Infers "healthy" as special requirement

2. **Conflicting requirements:**
   ```
   "Pescatarian vegan meal plan"
   ```
   - Returns warning about conflicting restrictions
   - Still generates plan (user decision)

---

## Supported Dietary Restrictions

- `vegan`
- `vegetarian`
- `pescatarian`
- `paleo`
- `keto`
- `gluten-free`
- `dairy-free`
- `nut-free`
- `soy-free`
- `halal`
- `kosher`
- `mediterranean`
- `dash`

## Supported Preferences

- `low-carb`
- `high-protein`
- `low-fat`
- `low-sodium`

## Supported Special Requirements

- `budget-friendly`
- `quick` (≤15 minutes)
- `easy` (simple preparation)
- `healthy` (nutritious/wholesome)

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request: [error message]"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "body": null
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate meal plan. Please try again."
}
```

---

## Caching

Meal plans are cached based on exact match of:
- Dietary restrictions
- Preferences
- Duration (days)
- Special requirements

Cache is persistent across server restarts (no expiration), but is not user-specific. The cache stores meal plans based solely on query parameters without any user identification. Identical queries from different users will return the same cached meal plan. Cache can be disabled via `ENABLE_CACHE=False` environment variable.

---

## Notes

- Maximum duration: 7 days (as per requirements)
- Snacks are included on even-numbered days (deterministic)
- Nutritional balance is considered across the week
- LLM validation can be disabled via `ENABLE_LLM_VALIDATION=False`
- Query dumps can be enabled for debugging via `ENABLE_QUERY_DUMP=True`

