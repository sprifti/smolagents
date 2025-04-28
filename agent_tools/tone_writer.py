from smolagents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai.llms import OpenAI


class ToneRewriter(Tool):
    name = "ToneRewriter"
    description = "Rewrites Albanian text in a given tone or provides multiple tone variations."
    inputs = {
        "text": {
            "type": "string",
            "description": "Albanian text",
        },
        "target_tone": {
            "type": "string",
            "description": "Required target tone to rewrite Albanian text",
        },
    }

    output_type = "string"

    def __init__(self):
        self.llm = OpenAI(temperature=0.2)

    def forward(self, text: str, target_tone: str):
        if target_tone:
            rewrite_template = """
            You are an expert Albanian language writer. Rewrite the following text to have a {target_tone} tone.
            Maintain the original meaning but change the style, word choice, and sentence structure to match the target tone.

            Original text: {text}

            Provide your rewrite as plain text with the following sections:

            ORIGINAL TONE:
            [Identification of the original tone]

            TARGET TONE:
            {target_tone}

            REWRITTEN TEXT:
            [The text rewritten in the target tone]
            
            The text should be in albanian.
            """

            prompt = PromptTemplate(
                input_variables=["text", "target_tone"],
                template=rewrite_template
            )
            self.tone_writer_chain = prompt | self.llm

            try:
                result = self.tone_writer_chain.invoke({"text": text, "target_tone": target_tone})
                return result
            except Exception as e:
                return {"error": str(e)}
        else:

            options_template = """
            You are an expert Albanian language writer. Provide three different tone variations of the following text.
            Each variation should have a distinct tone while maintaining the original meaning.

            Original text: {text}

            Provide your tone variations as plain text with the following sections:

            ORIGINAL TONE:
            [Identification of the original tone]

            FORMAL TONE VERSION:
            [Text rewritten in formal tone]

            FRIENDLY TONE VERSION:
            [Text rewritten in friendly tone]

            PERSUASIVE TONE VERSION:
            [Text rewritten in persuasive tone]
            
            The text should be in albanian.
            """

            prompt = PromptTemplate(input_variables=["text"], template=options_template)
            self.tone_writer_chain = prompt | self.llm

            try:
                result = self.tone_writer_chain.invoke({"text": text})
                return result
            except Exception as e:
                return {"error": str(e)}
