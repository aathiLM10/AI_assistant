from typing import Dict, Any


"""
Prompt templates decouple presentation and few-shot formatting from service orchestration logic.
Separating prompt construction ensures consistent token layout and enables dynamic injection
of constraints, context, and user inputs across diverse LLM tasks.
"""

class PromptTemplate:
    """
    Reusable template string formatter with validation of input variables.
    """
    def __init__(self, template: str, required_variables: list[str]):
        self.template = template
        self.required_variables = set(required_variables)

    def format(self, **kwargs: Any) -> str:
        missing = self.required_variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required template variables: {', '.join(missing)}")
        return self.template.format(**kwargs)


# Standard reusable query wrapper template ensuring clean prompt framing
USER_QUERY_TEMPLATE = PromptTemplate(
    template="""User Inquiry:
{user_query}

Provide a direct, high-quality, and structured response following the system guidance.""",
    required_variables=["user_query"]
)
