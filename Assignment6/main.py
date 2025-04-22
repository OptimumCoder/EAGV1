# main.py
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from perception import PerceptionModule
from memory import MemoryModule
from decision import DecisionModule
from action import ActionModule
from models import PerceptionType, DateTimeEncoder

load_dotenv()

class AgentSystem:
    def __init__(self, gemini_api_key: str):
        self.perception_module = PerceptionModule(gemini_api_key)
        self.memory_module = MemoryModule()
        self.decision_module = DecisionModule(gemini_api_key)
        self.action_module = ActionModule()

    async def initialize(self):
        """Initialize all necessary components."""
        await self.memory_module.initialize_db()

    async def process_input(self, input_data: str):
        """Process input through the entire agent system."""
        try:
            print("Before perception")
            # 1. Perception Phase
            perception = await self.perception_module.process_input(
                input_data, 
                PerceptionType.TEXT
            )
            print("After perception")
            enhanced_perception = await self.perception_module.enhance_perception(perception)
            
            # 2. Memory Phase
            await self.memory_module.store_memory(enhanced_perception)
            print("After Memory")
            relevant_memories = await self.memory_module.retrieve_relevant_memories(
                enhanced_perception.content
            )
            
            # 3. Decision Phase
            available_actions = list(self.action_module.available_actions.keys())
            decision = await self.decision_module.make_decision(
                enhanced_perception,
                relevant_memories,
                available_actions
            )
            
            # 4. Action Phase
            action_result = await self.action_module.execute_action(decision)
            
            # Convert all results to JSON-serializable format using the custom encoder
            result = {
                "perception": enhanced_perception.dict(),
                "decision": decision.dict(),
                "action_result": action_result.dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Verify JSON serialization
            return json.loads(json.dumps(result, cls=DateTimeEncoder))

        except Exception as e:
            return {
                "error": str(e),
                "phase": "process_input",
                "input_data": input_data,
                "timestamp": datetime.now().isoformat()
            }

def print_results(results: dict):
    """Pretty print the results with proper JSON formatting."""
    print("\nProcessing Results:")
    print(json.dumps(results, indent=2, cls=DateTimeEncoder))

async def main():
    try:
        # Get API key from environment variable
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("Please set GEMINI_API_KEY environment variable")

        # Initialize the agent system
        agent = AgentSystem(gemini_api_key)
        await agent.initialize()
        
        # Example input
        input_data = "Analyze the current market trends for AI technologies"
        
        # Process input
        result = await agent.process_input(input_data)
        
        # Print results
        if "error" in result:
            print(f"Error occurred: {result['error']}")
        else:
            print_results(result)

    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())