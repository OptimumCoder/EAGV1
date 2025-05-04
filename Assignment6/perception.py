# perception.py
from typing import Any, Dict
import google.generativeai as genai
from models import Perception, PerceptionType, LLMResponse, BaseModelWithJSON
from datetime import datetime
import json

class PerceptionModule:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.chat = self.model.start_chat(history=[])

    async def process_input(self, input_data: Any, input_type: PerceptionType) -> Perception:
        """Process incoming data using Gemini."""
        try:
            content = str(input_data) if not isinstance(input_data, str) else input_data
            
            # Generate initial response using Gemini
            response = await self.model.generate_content_async(content)

            # Create perception with timestamp
            perception = Perception(
                input_type=input_type,
                content=content,
                timestamp=datetime.now(),  # Explicitly set timestamp
                metadata={
                    "raw_type": str(type(input_data)),
                    "initial_analysis": response.text,
                    "length": len(content),
                    "word_count": len(content.split())
                }
            )
            return perception

        except Exception as e:
            # Create error perception with timestamp
            return Perception(
                input_type=input_type,
                content=content,
                timestamp=datetime.now(),  # Explicitly set timestamp
                metadata={
                    "error": str(e)
                }
            )

    async def enhance_perception(self, perception: Perception) -> Perception:
        """Enhance perception with detailed analysis using Gemini."""
        if perception.input_type == PerceptionType.TEXT:
            try:
                analysis_prompt = f"""
                Analyze the following input and provide a structured response in JSON format:
                
                Input: {perception.content}
                
                Please provide analysis in the following format:
                {{
                    "key_concepts": [],
                    "main_topics": [],
                    "entities": [],
                    "sentiment": "",
                    "intentions": [],
                    "implications": [],
                    "context": {{}},
                    "suggested_actions": []
                }}
                """

                response = await self.model.generate_content_async(analysis_prompt)

                try:
                    structured_analysis = json.loads(response.text)
                except json.JSONDecodeError:
                    structured_analysis = {"raw_analysis": response.text}

                llm_response = LLMResponse(
                    content=response.text,
                    metadata={
                        "model": "gemini-2.0-flash",
                        "analysis_type": "structured_enhancement"
                    },
                    timestamp=datetime.now()
                )

                perception.metadata["enhanced_analysis"] = structured_analysis
                perception.metadata["llm_response"] = llm_response.dict()

                # Update perception timestamp after enhancement
                perception.timestamp = datetime.now()

            except Exception as e:
                perception.metadata["enhancement_error"] = str(e)

        return perception