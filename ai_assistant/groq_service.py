# ai_assistant/groq_service.py

from groq import Groq
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GroqStudyAssistant:

    # Updated with ACTUAL models available on your Groq account
    VALID_MODELS = [
        # OpenAI open models (available on Groq)
        "openai/gpt-oss-120b",          # Large, powerful model
        "openai/gpt-oss-20b",           # Good balance of speed and quality
        "openai/gpt-oss-safeguard-20b", # Safety-focused version
        
        # Groq models
        "groq/compound",                # Groq's own compound model
        "groq/compound-mini",           # Lightweight version
        
        # Qwen models
        "qwen/qwen3.6-27b",             # Qwen 3.6 27B model
        
        # Other models
        "allam-2-7b",                   # Arabic support
        "canopylabs/orpheus-v1-english", # English Orpheus
        "canopylabs/orpheus-arabic-saudi", # Arabic Orpheus
        
        # Whisper models (for audio)
        "whisper-large-v3",
        "whisper-large-v3-turbo",
        
        # Llama Guard (for safety)
        "meta-llama/llama-prompt-guard-2-86m",
        "meta-llama/llama-prompt-guard-2-22m",
    ]

    # For backward compatibility - keep legacy models but they may not work
    LEGACY_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
    ]

    def __init__(self):
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            # Test which model works
            self.model = self._get_working_model()
            print(f"✅ Groq client initialized successfully with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None
            self.model = "openai/gpt-oss-20b"

    def _get_working_model(self):
        """Find a working model by testing each one"""
        if not self.client:
            return "openai/gpt-oss-20b"
        
        # Try current models first
        all_models = self.VALID_MODELS + self.LEGACY_MODELS
        
        for model in all_models:
            try:
                # Quick test to see if model works
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                logger.info(f"✅ Model {model} is working")
                return model
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        # If no model works, use the most reliable one
        return "openai/gpt-oss-20b"

    # ==========================================================
    # FALLBACK RESPONSES
    # ==========================================================

    def _fallback_response(self, fallback_type="tip"):
        fallbacks = {
            "tip": (
                "💡 **Study Tip**\n\n"
                "• Study for 25 minutes with full focus.\n"
                "• Take a 5-minute break.\n"
                "• Repeat the cycle four times."
            ),
            "quote": (
                "✨ **Daily Motivation**\n\n"
                "> Small daily improvements lead to amazing results over time."
            ),
            "resource": (
                "📚 **Recommended Resources**\n\n"
                "• **Khan Academy** - Free courses for many subjects.\n"
                "• **Coursera** - Free audit options for many courses.\n"
                "• **YouTube** - Educational videos and tutorials."
            ),
        }
        return fallbacks.get(fallback_type, fallbacks["tip"])

    def _make_request(self, messages, temperature=0.7, max_tokens=900):
        """Make a request to Groq API with automatic model fallback"""
        if not self.client:
            return None
        
        # Try models in order of preference (based on your available models)
        models_to_try = [
            self.model,
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "groq/compound",
            "groq/compound-mini",
            "allam-2-7b",
        ]
        
        last_error = None
        for model in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(f"✅ Request successful with model: {model}")
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        logger.error(f"All models failed. Last error: {last_error}")
        return None

    # ==========================================================
    # STUDY TIP
    # ==========================================================

    def get_study_tip(self, subject=None, struggle_level=None):
        if not self.client:
            return self._fallback_response("tip")

        prompt = f"""
You are a friendly and encouraging study assistant.

Give ONE short and practical study tip for:
{subject or 'general study'}

Maximum 15 words.
Be direct, useful, and easy for a student to understand.
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful study assistant. "
                    "Give concise and practical study tips."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self._make_request(messages, temperature=0.5, max_tokens=100)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("tip")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")

    # ==========================================================
    # MOTIVATIONAL QUOTE
    # ==========================================================

    def get_motivational_quote(self, mood="general"):
        if not self.client:
            return self._fallback_response("quote")

        prompt = f"""
Generate an encouraging motivational message for a student
who is feeling {mood}.

Requirements:
- Start with a bold heading.
- Include one motivational quote.
- Add 1 or 2 short sentences of encouragement.
- Keep the response clear and positive.
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You generate short, positive, and encouraging "
                    "motivational messages for students."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self._make_request(messages, temperature=0.8, max_tokens=400)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("quote")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("quote")

    # ==========================================================
    # RESOURCE RECOMMENDATION
    # ==========================================================

    def get_resource_recommendation(self, topic):
        if not self.client:
            return self._fallback_response("resource")

        prompt = f"""
Recommend 2 or 3 free online learning resources for:
{topic}

For each resource include:
- Resource name
- What it offers
- Why it is useful for beginners

Use clear formatting and short descriptions.
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You recommend useful learning resources "
                    "for students."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self._make_request(messages, temperature=0.5, max_tokens=800)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("resource")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("resource")

    # ==========================================================
    # ANSWER STUDY QUESTION
    # ==========================================================

    def answer_study_question(self, question, context=""):
        if not self.client:
            return self._fallback_response("tip")

        prompt = f"""
You are a helpful study assistant.

Student's question:
{question}

Additional context:
{context}

Requirements:
- Explain clearly.
- Use simple language.
- Use bullet points when useful.
- Use numbered steps for processes.
- Keep the answer organized.
- Add a short key takeaway at the end.
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a patient and knowledgeable "
                    "study assistant. Explain concepts clearly."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self._make_request(messages, temperature=0.7, max_tokens=900)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("tip")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")

    # ==========================================================
    # ANSWER QUESTION WITH CONVERSATION HISTORY
    # ==========================================================

    def answer_study_question_with_history(self, conversation_history):
        if not self.client:
            return self._fallback_response("tip")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a patient and knowledgeable study assistant. "
                    "Answer clearly using simple language, bullet points, "
                    "and numbered steps when useful."
                )
            }
        ]

        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        try:
            response = self._make_request(messages, temperature=0.7, max_tokens=900)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("tip")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")

    # ==========================================================
    # STUDY TIP WITH HISTORY
    # ==========================================================

    def get_study_tip_with_history(self, conversation_history):
        if not self.client:
            return self._fallback_response("tip")

        messages = [
            {
                "role": "system",
                "content": (
                    "You provide short, practical, and helpful study tips."
                )
            }
        ]

        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": (
                "Based on our conversation, give me one short and "
                "relevant study tip."
            )
        })

        try:
            response = self._make_request(messages, temperature=0.7, max_tokens=200)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("tip")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("tip")

    # ==========================================================
    # MOTIVATIONAL QUOTE WITH HISTORY
    # ==========================================================

    def get_motivational_quote_with_history(self, conversation_history):
        if not self.client:
            return self._fallback_response("quote")

        messages = [
            {
                "role": "system",
                "content": (
                    "You provide positive and encouraging motivational "
                    "messages for students."
                )
            }
        ]

        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": (
                "Give me a motivational message based on our conversation."
            )
        })

        try:
            response = self._make_request(messages, temperature=0.8, max_tokens=500)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("quote")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("quote")

    # ==========================================================
    # RESOURCE RECOMMENDATION WITH HISTORY
    # ==========================================================

    def get_resource_recommendation_with_history(self, topic, conversation_history):
        if not self.client:
            return self._fallback_response("resource")

        messages = [
            {
                "role": "system",
                "content": (
                    "You recommend useful and beginner-friendly "
                    "learning resources for students."
                )
            }
        ]

        for msg in conversation_history[-4:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": (
                f"Recommend 2 or 3 learning resources for {topic} "
                f"based on our conversation."
            )
        })

        try:
            response = self._make_request(messages, temperature=0.5, max_tokens=800)
            if response:
                return response.choices[0].message.content
            return self._fallback_response("resource")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response("resource")