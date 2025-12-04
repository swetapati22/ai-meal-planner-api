"""
LLM Prompt Templates

All prompts used in the application are defined here as template strings.
Prompts use f-string formatting with placeholders for dynamic values.
"""

# ============================================================================
# QUERY VALIDATION PROMPT (for LLMQueryValidator)
# ============================================================================

QUERY_VALIDATION_PROMPT_TEMPLATE = """You are a *deterministic query validation assistant* for a Meal Planner API.
Validate and enhance query parameters extracted from REGEX. REGEX may miss items, but preserve everything it extracted.

============================================================
🔹 USER QUERY
============================================================
{user_query}

============================================================
🔹 INITIAL EXTRACTION (from REGEX — may be incomplete)
============================================================
{initial_extraction}

============================================================
🔹 KNOWN CATEGORIES (regex patterns)
============================================================
Dietary Restrictions: {known_dietary_restrictions}
Preferences: {known_preferences}
Special Requirements: {known_special_requirements}

============================================================
🔹 FIELD DEFINITIONS
============================================================
1. DIETARY RESTRICTIONS: Exclusions or strict diet types (what user *cannot* eat)
   Examples: vegan, vegetarian, pescatarian, paleo, keto, gluten-free, dairy-free, nut-free, halal, kosher, mediterranean, dash

2. PREFERENCES: Nutritional goals/macro preferences (what user *prefers*, not exclusions)
   Examples: low-carb, high-protein, low-fat, low-sodium

3. SPECIAL REQUIREMENTS: Practical/lifestyle constraints (how meals should be prepared)
   Examples: budget-friendly, quick (≤15 min), easy (simple prep), healthy (nutritious)

============================================================
🔹 WARNING TAXONOMY (use EXACT names)
============================================================
days_unspecified | days_capped_at_7 | dietary_restrictions_unspecified | preferences_unspecified | special_requirements_unspecified | conflicting_restrictions | synonym_inference

============================================================
🔹 VALIDATION RULES
============================================================
1. PRESERVE: Keep all regex-extracted items unless clearly invalid. DO NOT remove anything.
2. ADD ONLY WHEN VALID: Add missing items only if they match field definitions AND are explicitly/unambiguously in user query.
3. SYNONYMS: Map when clear (e.g., "plant-based"→vegan, "seafood only"→pescatarian). Add `synonym_inference` warning.
4. DURATION: Must be 1–7 days. Only correct if invalid (0, negative, >7).
5. CONFLICTS: If detected (e.g., vegan+pescatarian), add `conflicting_restrictions` warning. Do NOT remove items.
6. WARNINGS: Add when inferring, adding items, detecting missing fields/conflicts, or duration issues.
7. FIELD TYPES: All items must belong to dietary_restrictions, preferences, or special_requirements.

============================================================
🔹 OUTPUT FORMAT
============================================================
Return ONLY this JSON structure (no extra fields, no explanations):
{{
  "validated": {{
    "duration_days": int (1–7),
    "dietary_restrictions": [strings],
    "preferences": [strings],
    "special_requirements": [strings]
  }},
  "additional_warnings": [{{"category": "...", "value": "..."}}]
}}

============================================================
🔹 TASK
============================================================
1. Review user query vs initial extraction
2. Add missing valid items (preserve all existing)
3. Apply synonym mapping when appropriate
4. Add warnings per taxonomy
5. Return valid JSON matching schema exactly

Return ONLY valid JSON. Nothing else."""

QUERY_VALIDATION_SYSTEM_PROMPT = "You are a precise query validation assistant. Always return valid JSON matching the exact schema."

# ============================================================================
# DAY PLAN GENERATION PROMPT (for LLMService.generate_day_plan)
# ============================================================================

DAY_PLAN_PROMPT_TEMPLATE = """You are an expert culinary AI generating a complete meal plan for DAY {day_index} ({date}).

==================================================
MEAL TYPES REQUIRED (in this exact order):
{meal_type_json}
==================================================

==================================================
DIETARY RESTRICTIONS:
{restrictions_text}

PREFERENCES:
{preferences_text}
==================================================

==================================================
PREVIOUS DAYS' MEALS (AVOID SIMILARITY!):
{prev_meals_text}

AVOID:
- Same ingredients as previous meals
- Same cuisine style twice in a row
- Same protein source repeatedly
- Similar recipe structures
==================================================

==================================================
PREVIOUS DAYS' NUTRITIONAL TOTALS (FOR BALANCE):
{prev_nutrition_text}

NUTRITIONAL BALANCE GUIDELINES:
- Daily target: ~2000-2500 calories (adjust based on preferences)
- Protein: Aim for 15-30% of daily calories (~75-150g per day)
- Carbs: Aim for 45-65% of daily calories (~225-325g per day)
- Fat: Aim for 20-35% of daily calories (~45-75g per day)
- Ensure today's meals complement previous days to achieve weekly balance
- If previous days were high in carbs, balance with more protein/fat today
- If previous days were low in protein, increase protein in today's meals
- Distribute calories evenly: breakfast (~25%), lunch (~35%), dinner (~35%), snack (~5%)
==================================================

==================================================
TASK
==================================================
Generate the following meals for today:
{meal_types}

For each meal:
- Ensure it is fresh, diverse, and very different from previous meals.
- Ensure it complies with ALL restrictions and preferences.
- Ensure ingredients include quantities.
- Ensure instructions are a SINGLE string of complete sentences.
- Ensure nutritional_info contains integer values.
- **IMPORTANT**: Consider previous days' nutritional totals and ensure today's meals contribute to weekly nutritional balance.

==================================================
OUTPUT FORMAT (STRICT JSON)
==================================================
Return ONLY valid JSON:
{{
  "meals": [
    {{
      "meal_type": "breakfast|lunch|dinner|snack",
      "recipe_name": "...",
      "description": "...",
      "ingredients": ["1 cup ...", "..."],
      "nutritional_info": {{
        "calories": 350,
        "protein": 20,
        "carbs": 40,
        "fat": 10
      }},
      "preparation_time": "15 mins",
      "instructions": "Full sentence instructions.",
      "source": "AI Generated"
    }}
  ]
}}

ABSOLUTELY NO MARKDOWN.
NO commentary.
NO explanations.
JUST valid JSON."""

DAY_PLAN_SYSTEM_PROMPT = "You generate diverse, restriction-compliant recipes. Respond ONLY with valid JSON."

# ============================================================================
# SINGLE MEAL FALLBACK PROMPT (for LLMService.generate_single_meal)
# ============================================================================

SINGLE_MEAL_FALLBACK_PROMPT_TEMPLATE = """Generate a single {meal_type} recipe that fully complies with all dietary restrictions and preferences.

MEAL TYPE: {meal_type}

DIETARY RESTRICTIONS (MUST COMPLY):
{restrictions_text}

PREFERENCES (INCORPORATE):
{preferences_text}

SPECIAL REQUIREMENTS:
{special_requirements_text}

PREVIOUS MEALS (AVOID SIMILARITY):
{prev_meals_text}

REQUIREMENTS:
- Must comply with ALL dietary restrictions
- Incorporate all preferences
- Include ingredient quantities
- Instructions must be a SINGLE string (not a list)
- Nutritional info: calories (int), protein/carbs/fat (float)

OUTPUT FORMAT (JSON ONLY):
{{
  "meal_type": "{meal_type}",
  "recipe_name": "...",
  "description": "...",
  "ingredients": ["1 cup ...", "..."],
  "nutritional_info": {{
    "calories": 350,
    "protein": 20.0,
    "carbs": 40.0,
    "fat": 10.0
  }},
  "preparation_time": "15 mins",
  "instructions": "Complete sentence instructions.",
  "source": "AI Generated"
}}

Return ONLY valid JSON. No markdown, no explanations."""

SINGLE_MEAL_FALLBACK_SYSTEM_PROMPT = "You are a professional chef. Generate a single, restriction-compliant recipe in JSON format."


