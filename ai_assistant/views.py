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
    # Clear conversation history when loading fresh page
    if 'conversation_history' in request.session:
        del request.session['conversation_history']
    
    context = {
        'user': request.user,
    }
    return render(request, 'ai_assistant/dashboard.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_api(request):
    """API endpoint for AI chat with memory"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        # Get or create conversation history from session
        if 'conversation_history' not in request.session:
            request.session['conversation_history'] = []
        
        conversation_history = request.session['conversation_history']
        
        # Add user message to history
        conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Keep only last 10 messages to avoid token limits
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        # Detect intent from user message
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['tip', 'advice', 'study better']):
            response_text = assistant.get_study_tip_with_history(conversation_history)
        elif any(word in message_lower for word in ['quote', 'motivate', 'encourage', 'motivation']):
            response_text = assistant.get_motivational_quote_with_history(conversation_history)
        elif any(word in message_lower for word in ['resource', 'video', 'tutorial', 'learn', 'course']):
            topic = user_message.replace('resource for', '').replace('find', '').replace('video', '').replace('tutorial', '').replace('learn', '').strip()
            response_text = assistant.get_resource_recommendation_with_history(topic or "studying", conversation_history)
        else:
            response_text = assistant.answer_study_question_with_history(conversation_history)
        
        # Add assistant response to history
        conversation_history.append({
            'role': 'assistant',
            'content': response_text
        })
        
        # Save back to session
        request.session['conversation_history'] = conversation_history
        
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
    return JsonResponse({'tip': tip, 'content': tip})

@login_required
def get_motivational_quote_api(request):
    """Get a motivational quote via API"""
    mood = request.GET.get('mood', 'general')
    quote = assistant.get_motivational_quote(mood)
    return JsonResponse({'quote': quote})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def clear_conversation(request):
    """Clear conversation history"""
    if 'conversation_history' in request.session:
        del request.session['conversation_history']
    return JsonResponse({'status': 'Conversation cleared'})