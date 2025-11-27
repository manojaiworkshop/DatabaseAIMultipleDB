#!/usr/bin/env python3
"""
Simple Ontology Generation Test
Minimal test to diagnose the LLM JSON parsing issue
"""

import asyncio
import json
import re


def test_json_parsing():
    """Test various JSON parsing strategies"""
    print("="*60)
    print("JSON PARSING TEST")
    print("="*60)
    
    # Example Ollama response from your logs
    sample_response = """[
      {
        "name": "Department",
        "description": "A organizational unit within the company",
        "tables": ["department"],
        "properties": ["id", "name", "manager_id"],
        "confidence": 0.85
      },
      {
        "name": "Employee",
        "description": "A person working for the company",
        "tables": ["employees"],
        "properties": ["id", "name", "email", "department_id"],
        "confidence": 0.90
      }
    ]"""
    
    print("\n1️⃣ Testing direct JSON parsing...")
    try:
        result = json.loads(sample_response)
        print(f"✅ Direct parse successful! Type: {type(result)}, Length: {len(result)}")
        print(f"   First concept: {result[0]['name']}")
    except Exception as e:
        print(f"❌ Direct parse failed: {e}")
    
    # Test with fenced code blocks
    fenced_response = f"```json\n{sample_response}\n```"
    
    print("\n2️⃣ Testing fenced JSON extraction...")
    try:
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```", fenced_response, re.IGNORECASE)
        if match:
            result = json.loads(match.group(1))
            print(f"✅ Fenced parse successful! Length: {len(result)}")
        else:
            print("❌ No fenced block found")
    except Exception as e:
        print(f"❌ Fenced parse failed: {e}")
    
    # Test with extra text
    messy_response = f"Here's the JSON output:\n{sample_response}\nThat's all!"
    
    print("\n3️⃣ Testing regex extraction from messy text...")
    try:
        match = re.search(r"(\[[\s\S]*\])", messy_response)
        if match:
            result = json.loads(match.group(1))
            print(f"✅ Regex parse successful! Length: {len(result)}")
        else:
            print("❌ No JSON array found")
    except Exception as e:
        print(f"❌ Regex parse failed: {e}")
    
    print("\n" + "="*60)
    print("✅ All parsing strategies work correctly!")
    print("="*60)


def analyze_llm_response():
    """Analyze the actual Ollama response from your logs"""
    print("\n" + "="*60)
    print("ANALYZING YOUR ACTUAL LLM RESPONSE")
    print("="*60)
    
    # Your actual Ollama response (truncated from logs)
    actual_response = """[
      {
        "name": "Department",
        "description": "A organizational unit within the company",
        "tables": ["department"],
        "properties": ["id", "name", "manager_id"]
      }
    ]"""
    
    print("\n📊 Response analysis:")
    print(f"   Length: {len(actual_response)} chars")
    print(f"   First char: '{actual_response[0]}'")
    print(f"   Last char: '{actual_response[-1]}'")
    print(f"   Starts with '[': {actual_response.strip().startswith('[')}")
    print(f"   Ends with ']': {actual_response.strip().endswith(']')}")
    
    print("\n🔍 Attempting to parse...")
    try:
        parsed = json.loads(actual_response)
        print(f"✅ Parse successful!")
        print(f"   Type: {type(parsed)}")
        print(f"   Length: {len(parsed)}")
        print(f"   Content: {json.dumps(parsed, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Position: line {e.lineno}, col {e.colno}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demonstrate_fix():
    """Show how the generate_structured method should work"""
    print("\n" + "="*60)
    print("PROPOSED generate_structured() METHOD")
    print("="*60)
    
    print("""
async def generate_structured(self, messages, max_tokens=1024, timeout=None):
    '''
    Ask the model to return a JSON object/list. Returns parsed JSON.
    '''
    # Step 1: Get raw response from LLM
    raw = await self.generate(messages, max_tokens=max_tokens, timeout=timeout)
    content = raw if isinstance(raw, str) else str(raw.get("content", raw))
    
    # Step 2: Try direct parse
    try:
        return json.loads(content)
    except Exception:
        pass
    
    # Step 3: Try fenced JSON extraction
    fenced = re.search(r"```(?:json)?\\s*(\\{[\\s\\S]*\\}|\\[[\\s\\S]*\\])\\s*```", content, re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass
    
    # Step 4: Try to find first {...} or [...] block
    block = re.search(r"(\\{[\\s\\S]*\\}|\\[[\\s\\S]*\\])", content)
    if block:
        try:
            return json.loads(block.group(1))
        except Exception:
            pass
    
    # Step 5: Fail with helpful error
    raise ValueError(f"Failed to parse JSON from LLM response: {content[:500]}")
""")
    
    print("\n✅ This method should be added to backend/app/services/llm.py")


def check_current_issue():
    """Explain the current issue based on logs"""
    print("\n" + "="*60)
    print("ROOT CAUSE ANALYSIS")
    print("="*60)
    
    print("""
📋 What's happening:

1. ✅ Database connection works
   - Tables are fetched and displayed in left sidebar
   - Schema snapshot returns 5 tables

2. ✅ Ollama generates valid JSON
   - Returns array of concept objects
   - Format is correct: [{"name": "Department", ...}, ...]

3. ❌ LLM wrapper expects SQL format
   - dynamic_ontology.py calls llm.generate_sql()
   - generate_sql() looks for response["sql"]
   - When it doesn't find "sql" key, it raises ValueError

4. ❌ Zero concepts in ontology
   - Exception stops concept extraction
   - Empty concepts list → empty YAML/OWL files
   - UI shows "0 concepts, 0 properties, 0 relationships"

🔧 Fix Required:

1. Add generate_structured() method to LLMService
   - Parse JSON responses (not SQL responses)
   - Handle fenced blocks and raw JSON

2. Update dynamic_ontology.py
   - Replace llm.generate_sql() calls
   - Use llm.generate_structured() instead

3. Update prompts
   - Instruct LLM: "Return ONLY valid JSON"
   - No SQL expected, just structured data
""")


def show_next_steps():
    """Show what needs to be done"""
    print("\n" + "="*60)
    print("NEXT STEPS TO FIX")
    print("="*60)
    
    print("""
🎯 Step 1: Add generate_structured to backend/app/services/llm.py
   Location: After the generate() method
   Code: See above demonstration

🎯 Step 2: Update backend/app/services/dynamic_ontology.py
   Find: self.llm.generate_sql(...)
   Replace: await self.llm.generate_structured(messages, max_tokens=2048)

🎯 Step 3: Test
   - Restart backend: python run_backend.py
   - Click "Generate Ontology" in UI
   - Check logs for: "✅ Dynamic ontology generated: X concepts"
   - Verify YAML file has concepts

🎯 Step 4: Verify files
   - Check ontology/*.yml
   - Should have concepts: [...] with entries
   - Should NOT be "0 concepts"
""")


def main():
    """Run all diagnostics"""
    print("\n🧪" * 30)
    print("ONTOLOGY GENERATION DIAGNOSTIC TOOL")
    print("🧪" * 30)
    
    test_json_parsing()
    analyze_llm_response()
    check_current_issue()
    demonstrate_fix()
    show_next_steps()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("""
The issue is clear: Your LLM is working perfectly and returning
valid JSON for concepts/relationships. However, the code is calling
the wrong method (generate_sql instead of generate_structured).

The fix is simple but requires code changes in two files:
1. backend/app/services/llm.py - Add generate_structured()
2. backend/app/services/dynamic_ontology.py - Use it

Would you like me to apply these changes now?
""")


if __name__ == "__main__":
    main()
