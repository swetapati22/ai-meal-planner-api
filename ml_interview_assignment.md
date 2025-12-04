# Machine Learning Engineer - Take-Home Assignment

## AI-Powered Personalized Meal Planner

**Time Allocation:** 2 days (48 hours from receipt)  
**Submission:** GitHub repository link with README and API documentation

---

## Problem Statement

Build a production-ready **AI Meal Planner API** that generates personalized, multi-day meal plans based on natural language user queries. Users should be able to request meal plans for 1-7 days with various dietary preferences, restrictions, and lifestyle requirements.

### Example User Queries
- *"Create a 5-day vegetarian meal plan with high protein"*
- *"I need a 3-day gluten-free meal plan, exclude dairy and nuts"*
- *"Generate a week of low-carb meals for two people, budget-friendly"*
- *"7-day Mediterranean diet plan with quick breakfast options"*

---

## Core Requirements

### 1. API Functionality

Build a REST API with the following endpoint:

**`POST /api/generate-meal-plan`**

**Request Format:**
```json
{
  "query": "string - natural language meal plan request"
}
```

**Response Format:**
```json
{
  "meal_plan_id": "unique_identifier",
  "duration_days": 5,
  "generated_at": "ISO timestamp",
  "meal_plan": [
    {
      "day": 1,
      "date": "2025-01-15",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "High-Protein Oatmeal Bowl",
          "description": "...",
          "ingredients": ["2 cups oats", "..."],
          "nutritional_info": {
            "calories": 350,
            "protein": 25,
            "carbs": 45,
            "fat": 8
          },
          "preparation_time": "15 mins",
          "instructions": "...",
          "source": "AI Generated | Recipe DB | URL"
        }
      ]
    }
  ],
  "summary": {
    "total_meals": 15,
    "dietary_compliance": ["vegetarian", "high-protein"],
    "estimated_cost": "$45-60",
    "avg_prep_time": "25 mins"
  }
}
```

### 2. Intelligent Query Processing

Your system must:
- Parse natural language queries to extract:
  - Duration (1-7 days)
  - Dietary restrictions (vegan, gluten-free, etc.)
  - Meal preferences (low-carb, high-protein, etc.)
  - Special requirements (budget-friendly, quick meals, etc.)
- Handle ambiguous or incomplete queries gracefully
- Provide sensible defaults when information is missing

### 3. Meal Plan Generation

Generate meal plans that:
- **Comply with all dietary restrictions and preferences**
- **Minimize recipe repetition** across days
- **Provide nutritional balance** across the week
- **Include realistic, cookable recipes** with:
  - Ingredient lists with quantities
  - Step-by-step cooking instructions
  - Estimated preparation time
  - Nutritional information
- **Vary meal types** (breakfast, lunch, dinner, optional snacks)

### 4. Recipe Sourcing

You may use any combination of:
- **AI/LLM generation** (GPT, Claude, Gemini, etc.)
- **Public recipe APIs** (Spoonacular, Edamam, TheMealDB, etc.)
- **Web scraping** (ensure legal compliance)
- **Hardcoded recipe database** (for demo purposes)
- **Hybrid approach** (recommended)

**Note:** Document your approach and any API keys involved.

---

## Technical Requirements

### Must-Have Features
1. ✅ Working REST API (FastAPI, Flask, Express, etc.)
2. ✅ Query parsing & intent extraction
3. ✅ Meal plan generation with recipe details
4. ✅ Error handling (invalid requests, API failures)
5. ✅ Basic input validation
6. ✅ API documentation (Swagger/OpenAPI preferred)
7. ✅ README with setup instructions

### Nice-to-Have Features (Bonus Points)
- 🌟 Recipe diversity algorithm (avoid repetitive meals)
- 🌟 Nutritional validation (ensure dietary compliance)
- 🌟 Caching mechanism (reduce API calls/cost)
- 🌟 Rate limiting
- 🌟 User preference storage (for `user_id` tracking)
- 🌟 Unit tests for critical components
- 🌟 Docker containerization
- 🌟 Cost optimization strategies
- 🌟 Observability (logging, monitoring)
- 🌟 Structured output validation (Pydantic, JSON Schema)

---

## Evaluation Criteria

Your submission will be evaluated on:

### 1. **Functionality (35%)**
- Does the API work as specified?
- Does it handle the example queries correctly?
- Are dietary restrictions respected?
- Are meal plans realistic and usable?

### 2. **ML/AI Engineering (25%)**
- Effective use of LLMs or ML techniques
- Prompt engineering quality (if using LLMs)
- Query parsing sophistication
- Recipe quality and diversity

### 3. **System Design (20%)**
- API architecture and design patterns
- Error handling and edge cases
- Scalability considerations
- Code organization and modularity

### 4. **Production Readiness (15%)**
- Code quality and best practices
- Documentation clarity
- Deployment feasibility
- Cost and performance considerations

### 5. **Creativity & Problem Solving (5%)**
- Novel approaches to constraints
- Trade-off decisions
- Handling of ambiguous requirements

---

## Submission Requirements

### 1. GitHub Repository
Your repository must include:
- **Source code** (well-organized, readable)
- **README.md** with:
  - Problem understanding
  - Architecture overview
  - Setup/installation instructions
  - How to run the API
  - Design decisions and trade-offs
  - Known limitations
  - Future improvements
- **API documentation** (Swagger UI, Postman collection, or detailed markdown)
- **Requirements file** (requirements.txt, package.json, etc.)
- **Environment variables template** (.env.example)

---

## Constraints & Guidelines

### Time Management
- **Expected effort:** 8-12 hours total
- **Scope appropriately** - we value working software over perfect software
- **Document what you would improve** given more time

### Technology Stack
- **No restrictions** - use what you're comfortable with
- **Popular choices:** Python (FastAPI/Flask), Node.js (Express), Go
- **LLM APIs:** OpenAI, Anthropic, Google Gemini, etc.
- **Recipe APIs:** Spoonacular, Edamam, etc. (be mindful of free tier limits)

### Cost Considerations
- Use only **free tiers**
- Implement **caching** to minimize API calls
- Consider **rate limiting** to prevent runaway costs

### What We're NOT Looking For
- ❌ Complex ML models trained from scratch
- ❌ Perfect UI/frontend (API only)
- ❌ Comprehensive test coverage (focus on critical paths)
- ❌ Production-grade infrastructure (Kubernetes, etc.)

### What We ARE Looking For
- ✅ Working, demonstrable solution
- ✅ Clean, readable code
- ✅ Thoughtful design decisions
- ✅ Good documentation
- ✅ Awareness of production concerns

---

## Testing Your Submission

We will test your API with queries like:

1. **Basic query:**  
   `"Create a 3-day vegetarian meal plan"`

2. **Complex query:**  
   `"Generate a 7-day low-carb, dairy-free meal plan with high protein, budget-friendly options, and quick breakfast recipes under 15 minutes"`

3. **Ambiguous query:**  
   `"I need healthy meals for next week"`

4. **Edge case:**  
   `"10-day vegan plan"` (exceeds 7-day limit)

5. **Conflicting requirements:**  
   `"Pescatarian vegan meal plan"` (contradictory)

Your API should handle all of these gracefully.

---

## Example Success Criteria

A **strong submission** will:
- ✅ Generate complete meal plans with all required fields
- ✅ Respect close to 100% of dietary restrictions
- ✅ Have <10% recipe repetition across 7 days
- ✅ Include detailed, realistic recipes
- ✅ Handle errors with informative messages
- ✅ Be runnable locally in <5 minutes
- ✅ Have clear, concise documentation

---

## Submission Process

1. **Complete your solution** within 48 hours
2. **Push code** to a **public** GitHub repository
3. **Email the repository link** to: ebundy@welldocinc.com
4. **Subject line:** "ML Engineer - Meal Planner Submission - [Your Name]"

Include in your email:
- GitHub repository link
- Estimated time spent
- Any questions or clarifications you needed

---

## Questions?

If you have questions during the assignment:
- **Preferred:** Document your assumptions in the README
- **If critical:** Email ebundy@welldocinc.com with subject "ML Assignment Question"

We typically respond within 4 hours during business hours.

---

## Evaluation Timeline

- **Submission deadline:** 48 hours from receipt
- **Initial review:** Within 3 business days
- **Technical interview:** Within 1 week (if selected)

During the technical interview, we'll discuss:
- Your design decisions
- Trade-offs you made
- How you would scale this to production
- Improvements you'd make with more time

---

## Tips for Success

1. **Start simple** - Get a basic working version first
2. **Iterate** - Add features incrementally
3. **Document as you go** - Don't leave it for the end
4. **Test your API** - Ensure it actually works before submitting
5. **Be honest** - Document limitations and what you'd improve
6. **Show your thinking** - We value transparency in decision-making

---

## Appendix: Useful Resources

### Recipe APIs (Free Tiers)
- **Spoonacular:** 150 requests/day free
- **Edamam:** 10,000 requests/month free (with attribution)
- **TheMealDB:** Free JSON API (limited recipes)
- **USDA FoodData Central:** Nutritional data

### LLM APIs
- **OpenAI:** $5 free credit for new accounts
- **Anthropic Claude:** Rate-limited free tier
- **Google Gemini:** Generous free tier

### Dietary Restriction Examples
- Vegan, vegetarian, pescatarian, paleo, keto
- Gluten-free, dairy-free, nut-free, soy-free
- Low-carb, high-protein, low-sodium, low-fat
- Halal, kosher, Mediterranean, DASH

---

**Good luck! We're excited to see your solution. 🚀**

*This assignment is designed to take 8-12 hours. Focus on demonstrating your ML engineering skills, system design thinking, and ability to ship working software.*