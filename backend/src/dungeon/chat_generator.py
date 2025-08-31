"""
Simple chat generator for conversational dungeon descriptions.
"""

import os

from langchain.schema import HumanMessage
from langchain_groq import ChatGroq


class ChatGenerator:
    """Handles conversational dungeon generation using GROQ API."""

    def __init__(self):
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.chat_model = None

        if self.groq_api_key:
            self.chat_model = ChatGroq(
                groq_api_key=self.groq_api_key,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            )

    def is_configured(self) -> bool:
        """Check if GROQ API is properly configured."""
        return self.chat_model is not None

    def generate_chat_response(self, user_message: str) -> dict[str, str]:
        """
        Generate a conversational dungeon description based on user input.

        Args:
            user_message: User's description of desired dungeon

        Returns:
            Dictionary containing the generated dungeon description

        Raises:
            ValueError: If GROQ API is not configured
            Exception: If generation fails
        """
        if not self.is_configured():
            raise ValueError("GROQ API not configured")

        if not user_message.strip():
            raise ValueError("User message cannot be empty")

        # Create a comprehensive dungeon generation prompt
        system_prompt = """You are an expert dungeon master and dungeon generator.
        Create detailed, immersive dungeon descriptions based on user requests.

        Your responses should include:
        - Detailed room descriptions with atmospheric details
        - Environmental elements (lighting, sounds, smells, temperature)
        - Potential challenges, traps, or puzzles
        - Creature encounters or NPCs if relevant
        - Treasure or loot locations
        - Hidden passages or secret areas
        - Overall dungeon layout and flow

        Focus on creating:
        - Immersive and atmospheric descriptions
        - Challenging but fair encounters
        - Creative and unique elements
        - Practical details for DMs to use

        Keep responses between 200-400 words, well-structured and easy to read."""

        # Combine system prompt with user message
        full_prompt = f"{system_prompt}\n\nUser request: {user_message}"

        # Generate response using GROQ
        messages = [HumanMessage(content=full_prompt)]
        response = self.chat_model.invoke(messages)
        generated_text = response.content

        return {
            "message": generated_text,
            "user_input": user_message,
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "status": "success",
        }

    def get_model_info(self) -> dict[str, str]:
        """Get information about the current model configuration."""
        return {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "provider": "GROQ",
            "configured": self.is_configured(),
        }
