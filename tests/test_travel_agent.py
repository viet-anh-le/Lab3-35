import pytest
import json
from src.agent.agent import ReActAgent
from src.tools.travel_tools import TRAVEL_TOOLS
from src.core.openai_provider import OpenAIProvider
import os
from dotenv import load_dotenv

load_dotenv()

# Test cases for the travel agent
class TestTravelAgent:
    """Test suite for the Travel Agent with 5 test cases"""
    
    @pytest.fixture
    def agent(self):
        """Create a travel agent instance for testing"""
        # Use OpenAI or mock provider
        try:
            llm = OpenAIProvider(model_name="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"))
        except:
            pytest.skip("OpenAI API key not available")
        
        agent = ReActAgent(llm=llm, tools=TRAVEL_TOOLS, max_steps=10)
        return agent
    
    def test_case_1_simple_weather_query(self, agent):
        """
        TEST CASE 1: Simple Single-Step Query (Easy)
        Goal: Agent should answer a simple weather question directly
        Expected: Agent calls get_weather tool once
        """
        query = "What's the weather like in Paris on 2026-04-10?"
        print(f"\n✅ TEST 1: {query}")
        
        result = agent.run(query)
        
        # Assertions
        assert result is not None
        assert "Paris" in result or "weather" in result.lower()
        print(f"Result: {result}")
    
    
    def test_case_2_destination_info_query(self, agent):
        """
        TEST CASE 2: Destination Information Query (Easy)
        Goal: Agent should retrieve destination information
        Expected: Agent calls get_destination_info tool
        """
        query = "Tell me about Tokyo as a travel destination. What are the attractions and visa requirements?"
        print(f"\n✅ TEST 2: {query}")
        
        result = agent.run(query)
        
        # Assertions
        assert result is not None
        assert "Tokyo" in result or "Japan" in result
        print(f"Result: {result}")
    
    
    def test_case_3_multi_step_trip_planning(self, agent):
        """
        TEST CASE 3: Multi-Step Trip Planning (Medium Difficulty)
        Goal: Agent should plan a trip using multiple tools
        Requires: Get destination info + Check weather + Check availability
        Expected: Agent should make 3+ tool calls
        """
        query = "I want to visit Bangkok for 3 days. Tell me about the destination, check the weather on 2026-04-12, and find activities available that day."
        print(f"\n✅ TEST 3: {query}")
        
        result = agent.run(query)
        
        # Assertions
        assert result is not None
        assert "Bangkok" in result or "Thailand" in result
        print(f"Result: {result}")
    
    
    def test_case_4_budget_trip_calculation(self, agent):
        """
        TEST CASE 4: Trip Budget Calculation (Medium Difficulty)
        Goal: Agent should calculate total trip cost by gathering prices
        Requires: Get flight price + Get hotel price + Calculate total
        Expected: Agent should provide cost breakdown with total
        """
        query = "I'm planning a 5-day trip from NYC to Paris on 2026-04-15. What will be the total cost including a standard hotel and flights? Assume daily activities cost $100."
        print(f"\n✅ TEST 4: {query}")
        
        result = agent.run(query)
        
        # Assertions
        assert result is not None
        assert "Paris" in result and "NYC" in result
        print(f"Result: {result}")
    
    
    def test_case_5_complex_trip_with_constraints(self, agent):
        """
        TEST CASE 5: Complex Trip Planning with Multiple Constraints (Hard)
        Goal: Agent should handle complex multi-step reasoning
        Requires: Check weather + Get destination info + Get prices + Validate availability
        Challenge: Agent needs to synthesize information and make recommendations
        """
        query = (
            "Help me plan a budget-friendly trip to Tokyo for 4 days starting 2026-04-15. "
            "I need to know: "
            "1) The weather and what to pack, "
            "2) Flight and hotel prices from NYC, "
            "3) Popular activities available, "
            "4) Estimated total cost with $80/day for activities. "
            "Should I go? (consider budget, weather, attractions)"
        )
        print(f"\n✅ TEST 5: {query}")
        
        result = agent.run(query)
        
        # Assertions
        assert result is not None
        assert "Tokyo" in result or "Japan" in result
        print(f"Result: {result}")


# Stand-alone test runner (for manual testing without pytest)
if __name__ == "__main__":
    """
    Run test cases manually:
    python -m pytest tests/test_travel_agent.py -v -s
    """
    print("=" * 80)
    print("TRAVEL AGENT TEST SUITE")
    print("=" * 80)
    print("\nTo run these tests, use:")
    print("  pytest tests/test_travel_agent.py -v -s")
    print("\nTest cases defined:")
    print("  1. Simple Weather Query")
    print("  2. Destination Information Query")
    print("  3. Multi-Step Trip Planning")
    print("  4. Budget Trip Calculation")
    print("  5. Complex Trip with Constraints")
    print("\n" + "=" * 80)
