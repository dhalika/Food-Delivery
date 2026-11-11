"""
AI Food Recommendations
Uses Groq LLM (gpt-oss-20b) to recommend food items based on user query
"""
import json
import logging
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from groq import Groq

from auth.guards import require_customer

logger = logging.getLogger('core')

GROQ_MODEL = 'openai/gpt-oss-20b'
MAX_MENU_ITEMS = 50  # Limit to avoid huge prompts
MAX_RECOMMENDATIONS = 3


# ==============================================================================
# DB HELPERS
# ==============================================================================
def get_menu_for_ai():
    """Fetch available menu items with restaurant info for AI context"""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.price,
                mi.is_veg,
                mi.image_url,
                r.id AS restaurant_id,
                r.name AS restaurant_name,
                0 AS restaurant_rating
            FROM menu_items mi
            INNER JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.is_available = 1
              AND r.is_active = 1
            ORDER BY mi.price ASC
            LIMIT %s
        """, [MAX_MENU_ITEMS])
        
        rows = cur.fetchall()
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in rows]


def get_items_by_ids(item_ids):
    """Fetch full item details for the recommended IDs"""
    if not item_ids:
        return []
    
    placeholders = ','.join(['%s'] * len(item_ids))
    with connection.cursor() as cur:
        cur.execute(f"""
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.price,
                mi.is_veg,
                mi.image_url,
                r.id AS restaurant_id,
                r.name AS restaurant_name,
                0 AS restaurant_rating
            FROM menu_items mi
            INNER JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.id IN ({placeholders})
              AND mi.is_available = 1
        """, item_ids)
        
        rows = cur.fetchall()
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in rows]


# ==============================================================================
# AI HELPERS
# ==============================================================================
def build_ai_prompt(user_query, menu_items):
    """Construct prompt with menu context for AI"""
    # Simplify menu for AI (only essential fields)
    simplified_menu = [
        {
            'id': str(item['id']),
            'name': item['name'],
            'desc': (item['description'] or '')[:80],
            'price': float(item['price']),
            'veg': bool(item['is_veg']),
            'restaurant': item['restaurant_name']
        }
        for item in menu_items
    ]
    
    prompt = f"""User wants: "{user_query}"

Available menu items:
{json.dumps(simplified_menu, indent=2)}

Analyze the user's request (spice level, budget, veg/non-veg, cuisine, mood) and pick the {MAX_RECOMMENDATIONS} BEST matching items.

Respond ONLY with valid JSON in this exact format:
{{
  "recommendations": [
    {{"item_id": "<id>", "reason": "<short reason why this matches user's need, max 15 words>"}},
    {{"item_id": "<id>", "reason": "<reason>"}},
    {{"item_id": "<id>", "reason": "<reason>"}}
  ]
}}"""
    return prompt


def call_groq_api(user_query, menu_items):
    """Call Groq LLM and get recommendations"""
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    prompt = build_ai_prompt(user_query, menu_items)
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                'role': 'system',
                'content': 'You are a food recommendation expert for HongKong food delivery app. Always respond with valid JSON only, no extra text.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={'type': 'json_object'}
    )
    
    ai_text = response.choices[0].message.content
    logger.info(f"AI raw response: {ai_text[:200]}")
    
    return json.loads(ai_text)


def enrich_recommendations(ai_response, menu_items):
    """Merge AI's picks with full item details from DB"""
    recommendations = ai_response.get('recommendations', [])
    
    # Build lookup for reasons
    reasons_map = {str(r.get('item_id')): r.get('reason', '') for r in recommendations}
    
    # Fetch full item details
    item_ids = list(reasons_map.keys())
    items = get_items_by_ids(item_ids)
    
    # Combine
    enriched = []
    for item in items:
        enriched.append({
            'item_id': str(item['id']),
            'name': item['name'],
            'description': item['description'],
            'price': float(item['price']),
            'is_veg': bool(item['is_veg']),
            'image_url': item['image_url'],
            'restaurant_id': str(item['restaurant_id']),
            'restaurant_name': item['restaurant_name'],
            'restaurant_rating': float(item['restaurant_rating'] or 0),
            'ai_reason': reasons_map.get(str(item['id']), 'Recommended for you')
        })
    
    return enriched


def fallback_recommendations():
    """When AI fails, return top-rated items"""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.price,
                mi.is_veg,
                mi.image_url,
                r.id AS restaurant_id,
                r.name AS restaurant_name,
                0 AS restaurant_rating
            FROM menu_items mi
            INNER JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.is_available = 1
              AND r.is_active = 1
            ORDER BY mi.created_at DESC
            LIMIT %s
        """, [MAX_RECOMMENDATIONS])
        
        rows = cur.fetchall()
        columns = [col[0] for col in cur.description]
        items = [dict(zip(columns, row)) for row in rows]
    
    return [{
        'item_id': str(item['id']),
        'name': item['name'],
        'description': item['description'],
        'price': float(item['price']),
        'is_veg': bool(item['is_veg']),
        'image_url': item['image_url'],
        'restaurant_id': str(item['restaurant_id']),
        'restaurant_name': item['restaurant_name'],
        'restaurant_rating': float(item['restaurant_rating'] or 0),
        'ai_reason': 'Top-rated pick from our menu'
    } for item in items]


# ==============================================================================
# VIEWS
# ==============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_customer
def ai_recommend_view(request):
    """
    AI Food Recommendation endpoint
    POST /api/customer/ai-recommend/
    Body: { "query": "I want something spicy under 300" }
    """
    try:
        # Parse request
        body = json.loads(request.body)
        user_query = (body.get('query') or '').strip()
        
        if not user_query:
            return JsonResponse({
                'success': False,
                'error': 'Query is required'
            }, status=400)
        
        if len(user_query) > 300:
            return JsonResponse({
                'success': False,
                'error': 'Query too long (max 300 chars)'
            }, status=400)
        
        logger.info(f"AI query from user {request.user_id}: {user_query}")
        
        # Fetch menu
        menu_items = get_menu_for_ai()
        if not menu_items:
            return JsonResponse({
                'success': False,
                'error': 'No menu items available right now'
            }, status=404)
        
        # Call AI
        try:
            ai_response = call_groq_api(user_query, menu_items)
            recommendations = enrich_recommendations(ai_response, menu_items)
            
            if not recommendations:
                logger.warning("AI returned empty recommendations, using fallback")
                recommendations = fallback_recommendations()
                
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}")
            recommendations = fallback_recommendations()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            recommendations = fallback_recommendations()
        
        return JsonResponse({
            'success': True,
            'query': user_query,
            'recommendations': recommendations,
            'count': len(recommendations)
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        logger.exception(f"AI recommend error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong. Please try again.'
        }, status=500)


# ==============================================================================
# URL PATTERNS
# ==============================================================================
urlpatterns = [
    path('customer/ai-recommend/', ai_recommend_view, name='ai_recommend'),
]