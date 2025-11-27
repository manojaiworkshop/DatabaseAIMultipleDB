#!/usr/bin/env python3
"""
Test OpenAI Integration
"""
import yaml
from backend.app.services.llm import LLMService

# Load config
with open('app_config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Test with OpenAI
print("Testing OpenAI integration...")
print(f"Provider: {config['llm']['provider']}")
print(f"OpenAI Model: {config['openai']['model']}")
print(f"OpenAI API Key (first 20 chars): {config['openai']['api_key'][:20]}...")

try:
    # Create LLM service
    llm_service = LLMService(config)
    print(f"✅ LLM Service initialized successfully")
    print(f"Current provider: {llm_service.current_provider}")
    
    # Test simple schema context
    test_schema = """
    Table: users
    Columns:
    - id (integer, primary key)
    - name (text)
    - email (text)
    """
    
    # Test query
    test_question = "How many users are there?"
    
    print(f"\nTest Question: {test_question}")
    print("Generating SQL...")
    
    result = llm_service.generate_sql(test_question, test_schema)
    
    print(f"\n✅ SUCCESS!")
    print(f"SQL: {result['sql']}")
    print(f"Explanation: {result.get('explanation', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
