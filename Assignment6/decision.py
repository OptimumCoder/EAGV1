# decision.py
from typing import List, Dict, Any
from google import genai
from models import Decision, Memory, Perception
import uuid

class DecisionModule:
    def __init__(self, llm_api_key: str):
        self.llm_api_key = llm_api_key
        genai.api_key = llm_api_key

    async def make_decision(
        self, 
        current_perception: Perception,
        relevant_memories: List[Memory],
        available_actions: List[str]
    ) -> Decision:
        """Make a decision based on current perception and memories."""
        
        # Prepare context for LLM
        context = self._prepare_context(current_perception, relevant_memories)
        
        # Get decision from LLM
        try:
            response = await genai.ChatCompletion.create(
                model="gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": "You are a decision-making AI. Based on the context and available actions, select the most appropriate action and provide reasoning."},
                    {"role": "user", "content": self._format_decision_prompt(context, available_actions)}
                ]
            )
            
            # Parse LLM response
            decision_content = response.choices[0].message.content
            selected_action, reasoning = self._parse_llm_response(decision_content)
            
            # Create decision object
            decision = Decision(
                id=str(uuid.uuid4()),
                context=context,
                options=available_actions,
                selected_option=selected_action,
                confidence_score=self._calculate_confidence(response),
                reasoning=reasoning
            )
            
            return decision
            
        except Exception as e:
            # Fallback decision if LLM fails
            return self._make_fallback_decision(available_actions, str(e))

    def _prepare_context(
        self, 
        perception: Perception,
        memories: List[Memory]
    ) -> Dict:
        """Prepare context for decision making."""
        return {
            "current_perception": perception.dict(),
            "relevant_memories": [memory.dict() for memory in memories],
            "timestamp": perception.timestamp.isoformat()
        }

    def _format_decision_prompt(self, context: Dict, available_actions: List[str]) -> str:
        """Format the prompt for the LLM."""
        prompt = f"""
        Current Situation:
        {context['current_perception']['content']}
        
        Relevant Past Information:
        {self._format_memories(context['relevant_memories'])}
        
        Available Actions:
        {', '.join(available_actions)}
        
        Please select the most appropriate action and provide your reasoning.
        Format your response as:
        Selected Action: <action>
        Reasoning: <your reasoning>
        """
        return prompt

    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for the prompt."""
        return "\n".join([f"- {memory['content']}" for memory in memories])

    def _parse_llm_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract action and reasoning."""
        lines = response.split('\n')
        action = ""
        reasoning = ""
        
        for line in lines:
            if line.startswith("Selected Action:"):
                action = line.replace("Selected Action:", "").strip()
            elif line.startswith("Reasoning:"):
                reasoning = line.replace("Reasoning:", "").strip()
                
        return action, reasoning

    def _calculate_confidence(self, llm_response: Any) -> float:
        """Calculate confidence score for the decision."""
        # Implement confidence calculation logic
        # This is a simple example
        return 0.8

    def _make_fallback_decision(self, available_actions: List[str], error: str) -> Decision:
        """Make a fallback decision when LLM fails."""
        return Decision(
            id=str(uuid.uuid4()),
            context={"error": error},
            options=available_actions,
            selected_option=available_actions[0],
            confidence_score=0.1,
            reasoning="Fallback decision due to LLM error"
        )