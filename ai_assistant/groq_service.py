# ai_assistant/groq_service.py
from groq import Groq
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GroqStudyAssistant:
    def __init__(self):
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            # Use a model that is actually available
            self.model_name = "openai/gpt-oss-120b"  # Changed from llama-3.3-70b-versatile
            print(f"✅ Groq client initialized successfully with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None
    
    def _fallback_response(self, fallback_type="tip"):
        """Return a local response when API is unavailable"""
        fallbacks = {
            "tip": "💡 **The Pomodoro Technique**\n\n• 25 minutes focused study\n• 5 minute break\n• Repeat 4 times\n• Take longer 15-30 min break",
            "quote": "✨ **Daily Motivation**\n\n> Small daily improvements lead to amazing results over time.",
            "resource": "📚 **Recommended Resources**\n\n• **Khan Academy** - Free courses on every subject\n• **Coursera** - Free audit options for many courses\n• **YouTube** - Countless educational channels",
        }
        return fallbacks.get(fallback_type, fallbacks["tip"])
    
    def get_study_tip(self, subject=None, struggle_level=None):
        """Generate a personalized study tip with formatting"""
        if not self.client:
            return self._fallback_response("tip")
        
        prompt = f"""
        You are a friendly, encouraging study assistant for students.
         Give ONE very short, concise study tip for {subject or 'general subjects'}.
    Maximum 15 words. Be direct and practical.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant. ALWAYS format your responses with a clear, concise tip. Keep it under 15 words."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")
    
    def get_motivational_quote(self, mood="general"):
        """Generate a motivational quote with formatting"""
        if not self.client:
            return self._fallback_response("quote")
        
        prompt = f"""
        Generate an encouraging motivational message for a student who is feeling {mood}.
        
        FORMATTING REQUIREMENTS:
        - Start with a **bold heading** like **✨ Today's Motivation**
        - Put the main quote in > quote format
        - Add 1-2 sentences of encouragement below
        - Use line breaks for clarity
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=[
                    {"role": "system", "content": "You generate motivational messages. ALWAYS use **bold headers**, > for quotes, and clean formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500  # Increased from 400
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("quote")
    
    def get_resource_recommendation(self, topic):
        """Recommend learning resources with formatting"""
        if not self.client:
            return self._fallback_response("resource")
        
        prompt = f"""
        Recommend 2-3 free online resources to help a student learn "{topic}".
        
        FORMATTING REQUIREMENTS:
        - Use **bold** for resource titles
        - Format each resource as:
          **📚 Resource Name**
          • What it offers
          • Why it's good for beginners
          • Where to find it
        
        Separate resources with blank lines.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=[
                    {"role": "system", "content": "You recommend learning resources. ALWAYS format with **bold titles**, bullet points (•), and clear separation between resources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("resource")
    
    def answer_study_question(self, question, context=""):
        """Answer a student's study-related question with formatting"""
        if not self.client:
            return self._fallback_response("tip")
        
        prompt = f"""
        You are a patient, knowledgeable study assistant for students.
        
        Student's question: {question}
        
        FORMATTING REQUIREMENTS:
        - Use **bold** for key terms and headings
        - Use bullet points (•) for lists
        - Use numbered steps (1., 2., 3.) for processes
        - Use > for important quotes or key takeaways
        - Break content into short paragraphs
        - Add a "📌 Key Takeaway" section at the end
        
        Make the response visually organized and easy to scan.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=[
                    {"role": "system", "content": "You are a study assistant. ALWAYS format responses with **bold headers**, bullet points (•), numbered steps, clear sections, and a final key takeaway. Make responses beautiful and readable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=900
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")
    
    # ========== METHODS WITH HISTORY (CONVERSATION MEMORY) ==========
    
    def answer_study_question_with_history(self, conversation_history):
        """Answer with conversation context and formatting"""
        if not self.client:
            return self._fallback_response("tip")
        
        messages = [
            {"role": "system", "content": "You are a patient, knowledgeable study assistant. ALWAYS format responses with:\n- **Bold headers** for sections\n- • Bullet points for lists\n- 1., 2., 3. for steps\n- > for key takeaways\n- Clear line breaks\nMake responses visually organized and easy to scan."}
        ]
        
        for msg in conversation_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=messages,
                temperature=0.7,
                max_tokens=900
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")
    
    def get_study_tip_with_history(self, conversation_history):
        """Generate study tip with context and formatting"""
        if not self.client:
            return self._fallback_response("tip")
        
        messages = [
            {"role": "system", "content": "You provide study tips. ALWAYS format with **bold headers**, bullet points (•), and clear organization."}
        ]
        
        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        messages.append({
            "role": "user",
            "content": "Based on our conversation, give me a relevant study tip with proper formatting (bold headers, bullet points)."
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")
    
    def get_motivational_quote_with_history(self, conversation_history):
        """Generate motivational quote with context and formatting"""
        if not self.client:
            return self._fallback_response("quote")
        
        messages = [
            {"role": "system", "content": "You provide motivational messages. Use **bold headers** and > for quote formatting."}
        ]
        
        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        messages.append({
            "role": "user",
            "content": "Give me a motivational message based on our conversation with proper formatting."
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("quote")
    
    def get_resource_recommendation_with_history(self, topic, conversation_history):
        """Recommend resources with context and formatting"""
        if not self.client:
            return self._fallback_response("resource")
        
        messages = [
            {"role": "system", "content": "You recommend learning resources. Format with **bold titles** and bullet points (•)."}
        ]
        
        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        messages.append({
            "role": "user",
            "content": f"Recommend resources for {topic} based on our conversation. Use proper formatting with bold headers and bullet points."
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Changed to use self.model_name
                messages=messages,
                temperature=0.5,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("resource")