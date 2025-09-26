import os
import time
from typing import List, Dict
import google.generativeai as genai

class DebateAIService:
    """
    AI service that uses the Google Gemini API to generate
    dynamic and contextual debate responses.
    """
    
    def __init__(self):
        """
        Initializes the Gemini AI model.
        """
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
            genai.configure(api_key=api_key)
            
            self.model = genai.GenerativeModel(model_name="text-bison-001")
            print("--- Google Gemini AI Service Initialized Successfully with model: text-bison-001 ---")


        except Exception as e:
            print(f"--- ERROR: Failed to initialize Gemini AI Service: {e} ---")
            self.model = None

    def generate_response(self, user_message: str, topic: str, difficulty: str, 
                         conversation_history: List[Dict]) -> Dict:
        """
        Generates a contextual debate response using the generative model.
        """
        start_time = time.time()
        
        if not self.model:
            return {
                'content': "I'm currently unable to connect to my AI core. Please try again later.", 
                'response_time': 0, 
                'sender': 'ai'
            }

        temperature = 0.7
        if difficulty == 'medium':
            temperature = 0.85
        elif difficulty == 'hard':
            temperature = 1.0
            
        generation_config = {
            "temperature": temperature,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }

        prompt = self._build_prompt(user_message, topic, difficulty, conversation_history)
        
        try:
            # Send the prompt and the new config to the AI model
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            ai_content = response.text.strip()
        except Exception as e:
            print(f"--- ERROR: Gemini API call failed: {e} ---")
            ai_content = "I'm having a bit of trouble formulating a response right now. Could you please rephrase your argument?"

        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return {'content': ai_content, 'response_time': response_time, 'sender': 'ai'}

    def _build_prompt(self, user_message: str, topic: str, difficulty: str,
                      conversation_history: List[Dict]) -> str:
        """Constructs a detailed prompt for the AI model."""

        history_str = "\n".join(
            [f"- {msg['sender'].upper()}: {msg['content']}" for msg in conversation_history[-4:]]
        )

        difficulty_instructions = {
            'easy': "Your persona is that of a friendly beginner. Use simple language and make one clear, straightforward point. Avoid complex vocabulary and concepts. Your goal is to have an accessible discussion.",
            'medium': "Your persona is that of a knowledgeable peer. Your arguments should be well-reasoned and logical. You can introduce related concepts or general evidence to support your point. Your goal is a balanced, intelligent debate.",
            'hard': "Your persona is that of an expert debater. Your arguments should be sharp, analytical, and directly challenge the user's logic. You can point out fallacies, use advanced vocabulary, and introduce complex, multi-layered counter-arguments. Your goal is to win the debate decisively."
        }
        
        prompt = f"""You are Debato AI, a formidable and intelligent debate opponent.
The topic of this debate is: "{topic}"

**Your Persona and Instructions for this round (Difficulty: {difficulty.upper()}):**
{difficulty_instructions.get(difficulty, "")}

**General Rules:**
1. Analyze the user's last message and the conversation history.
2. You must take an opposing stance to the user.
3. Generate a strong, concise counter-argument based on your persona. Your response must be short, around 2-4 sentences.
4. Do not agree with the user or concede points.

---
CONVERSATION HISTORY (Most recent messages):
{history_str}

USER'S LATEST ARGUMENT: "{user_message}"
---

Now, generate your counter-argument based on your assigned persona and instructions:
"""
        return prompt