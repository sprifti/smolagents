from smolagents import Tool
from langchain.prompts import PromptTemplate
from langchain_openai.llms import OpenAI


class ToneAnalyzer(Tool):
    name = "ToneAnalyzer"
    description = "Analyzes tone, formality, and sentiment of Albanian text."
    inputs = {
        "text": {
            "type": "string",
            "description": "Albanian text",
        }
    }

    output_type = "string"

    def __init__(self):
        self.llm = OpenAI(temperature=0)

        tone_template = """
        You are an expert in analyzing the tone and sentiment of Albanian language text.
        Analyze the following text and identify its tone, formality level, and overall sentiment.

        Text to analyze: {text}

        Provide your analysis as plain text with the following sections:

        TONE:
        [Primary tone (formal, informal, friendly, aggressive, neutral, etc.)]

        FORMALITY LEVEL:
        [Rating on a scale of 1-5 where 1 is very informal and 5 is very formal]

        SENTIMENT:
        [Positive, negative, or neutral]

        TONE ANALYSIS:
        [Brief explanation of tone characteristics]
        """

        tone_prompt = PromptTemplate(
            input_variables=["text"],
            template=tone_template
        )

        self.tone_chain = tone_prompt | self.llm

    def forward(self, text: str):
        try:
            result = self.tone_chain.invoke({"text": text})
            return result
        except Exception as e:
            return {"error": str(e)}
