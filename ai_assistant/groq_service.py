# ai_assistant/groq_service.py
from groq import Groq
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GroqStudyAssistant:
    def __init__(self):
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            print("✅ Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None
    
    def _fallback_response(self, fallback_type="tip"):
        """Return a local response when API is unavailable"""
        fallbacks = {
            "tip": "💡 The Pomodoro Technique: 25 minutes study, 5 minutes break. Try it!",
            "quote": "✨ Small daily improvements lead to amazing results over time.",
            "resource": "📚 Check out Khan Academy or Coursera for free courses!",
        }
        return fallbacks.get(fallback_type, fallbacks["tip"])
    
    def get_study_tip(self, subject=None, struggle_level=None):
        """Generate a personalized study tip"""
        if not self.client:
            return self._fallback_response("tip")
        
        prompt = f"""
        You are a friendly, encouraging study assistant for students.
        
        Give ONE short, actionable study tip for a student learning {subject or 'general subjects'}.
        
        Keep it under 5 sentences. Be specific and practical.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant. Keep responses concise and practical."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")
    
    def get_motivational_quote(self, mood="general"):
        """Generate a motivational quote based on mood"""
        if not self.client:
            return self._fallback_response("quote")
        
        prompt = f"""
        Generate an original, short motivational quote for a student who is feeling {mood}.
        
        Keep it under 20 words. Be encouraging but not cliché.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You generate short, original motivational quotes for students."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("quote")
    
    def get_resource_recommendation(self, topic):
        """Recommend learning resources for a specific topic"""
        if not self.client:
            return self._fallback_response("resource")
        
        prompt = f"""
        Recommend ONE free online resource to help a student learn "{topic}".
        
        Format your response as:
        TITLE: [resource name]
        WHY: [one sentence why it's good for beginners]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You recommend free, trustworthy educational resources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("resource")
    
    def answer_study_question(self, question, context=""):
        """Answer a student's study-related question"""
        if not self.client:
            return self._fallback_response("tip")
        
        prompt = f"""
        You are a patient, knowledgeable study assistant for students.
        
        Student's question: {question}
        
        Provide a helpful, accurate answer. Keep it concise (3-4 sentences max).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant. Provide clear, accurate answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "I'm having trouble connecting right now. Please try again in a moment!"