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

        return fallbacks.get(
            fallback_type,
            fallbacks["tip"]
        )


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

        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
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
                ],

                temperature=0.5,
                max_tokens=100
            )

            return response.choices[0].message.content

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

        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
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
                ],

                temperature=0.8,
                max_tokens=400
            )

            return response.choices[0].message.content

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

        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
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
                ],

                temperature=0.5,
                max_tokens=800
            )

            return response.choices[0].message.content

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

        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
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
                ],

                temperature=0.7,
                max_tokens=900
            )

            return response.choices[0].message.content

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

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,

                temperature=0.7,
                max_tokens=900
            )

            return response.choices[0].message.content

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

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,

                temperature=0.7,
                max_tokens=200
            )

            return response.choices[0].message.content

        except Exception as e:

            logger.error(f"Groq API error: {e}")

            return self._fallback_response("tip")


    # ==========================================================
    # MOTIVATIONAL QUOTE WITH HISTORY
    # ==========================================================

    def get_motivational_quote_with_history(
        self,
        conversation_history
    ):

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

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,

                temperature=0.8,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:

            logger.error(f"Groq API error: {e}")

            return self._fallback_response("quote")


    # ==========================================================
    # RESOURCE RECOMMENDATION WITH HISTORY
    # ==========================================================

    def get_resource_recommendation_with_history(
        self,
        topic,
        conversation_history
    ):

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

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,

                temperature=0.5,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:

            logger.error(f"Groq API error: {e}")

            return self._fallback_response("resource")