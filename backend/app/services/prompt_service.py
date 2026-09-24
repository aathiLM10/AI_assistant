from typing import Tuple
from app.prompts.system import SYSTEM_PROMPT
from app.prompts.templates import USER_QUERY_TEMPLATE


"""
PromptService is responsible for assembling, structuring, and decorating prompts.
In generative AI workflows, separating prompt construction from execution allows dynamic
context injection, prompt versioning, and testing of prompts independently of network calls.
"""

class PromptService:
    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        self.system_prompt = system_prompt

    def build_prompt(self, user_query: str) -> Tuple[str, str]:
        """
        Builds the formatted user prompt and retrieves the active system prompt.
        Returns:
            Tuple[user_formatted_prompt, system_instruction]
        """
        formatted_user_prompt = USER_QUERY_TEMPLATE.format(user_query=user_query)
        return formatted_user_prompt, self.system_prompt
