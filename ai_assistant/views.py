# ai_assistant/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .groq_service import GroqStudyAssistant

# Initialize the assistant once (reused across requests)
assistant = GroqStudyAssistant()

@login_required
def ai_assistant_dashboard(request):
    """Main AI Assistant view"""
    # Get a quick tip for the sidebar
    daily_tip = assistant.get_study_tip()
    
    context = {
        'daily_tip': daily_tip,
        'user': request.user,
    }
    return render(request, 'ai_assistant/dashboard.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_api(request):
    """API endpoint for AI chat"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        # Detect intent from user message (simple keyword matching)
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['tip', 'advice', 'study better']):
            response_text = assistant.get_study_tip()
            
        elif any(word in message_lower for word in ['quote', 'motivate', 'encourage', 'motivation']):
            response_text = assistant.get_motivational_quote()
            
        elif any(word in message_lower for word in ['resource', 'video', 'tutorial', 'learn', 'course']):
            # Extract topic (simplified)
            topic = user_message.replace('resource for', '').replace('find', '').replace('video', '').replace('tutorial', '').replace('learn', '').strip()
            response_text = assistant.get_resource_recommendation(topic or "studying")
            
        else:
            response_text = assistant.answer_study_question(user_message)
        
        return JsonResponse({
            'message': response_text,
            'suggestions': ["Give me a study tip", "Motivate me", "Find a resource"]
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_study_tip_api(request):
    """Get a study tip via API"""
    subject = request.GET.get('subject', None)
    tip = assistant.get_study_tip(subject)
    return JsonResponse({'content': tip, 'tip': tip})

@login_required
def get_motivational_quote_api(request):
    """Get a motivational quote via API"""
    mood = request.GET.get('mood', 'general')
    quote = assistant.get_motivational_quote(mood)
    return JsonResponse({'quote': quote})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def get_resource_api(request):
    """Get resource recommendation via API"""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', 'studying')
        resource = assistant.get_resource_recommendation(topic)
        return JsonResponse({'resource': resource})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)