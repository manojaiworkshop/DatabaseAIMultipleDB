"""
Test Context Manager with different token limits

This script tests the ContextManager with various max_token configurations
to ensure it properly adjusts context verbosity.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.context_manager import ContextManager, ContextStrategy
from colorama import Fore, Style, init

init(autoreset=True)


def print_section(title):
    """Print a colored section header"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{title}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


def test_strategy_selection():
    """Test automatic strategy selection"""
    print_section("TEST 1: Automatic Strategy Selection")
    
    test_cases = [
        (2000, ContextStrategy.CONCISE),
        (4000, ContextStrategy.SEMI_EXPANDED),
        (8000, ContextStrategy.EXPANDED),
        (16000, ContextStrategy.LARGE),
    ]
    
    for max_tokens, expected_strategy in test_cases:
        cm = ContextManager(max_tokens=max_tokens, strategy="auto")
        
        if cm.strategy == expected_strategy:
            print(f"{Fore.GREEN}✓ {max_tokens} tokens -> {cm.strategy.value} (correct)")
        else:
            print(f"{Fore.RED}✗ {max_tokens} tokens -> {cm.strategy.value} (expected {expected_strategy.value})")
        
        stats = cm.get_context_stats()
        print(f"  Budget: schema={stats['budgets']['schema']}, "
              f"error={stats['budgets']['error_context']}, "
              f"system={stats['budgets']['system_prompt']}")


def test_system_prompts():
    """Test system prompt generation at different levels"""
    print_section("TEST 2: System Prompt Generation")
    
    for max_tokens in [2000, 4000, 8000, 16000]:
        cm = ContextManager(max_tokens=max_tokens, strategy="auto")
        prompt = cm.build_system_prompt()
        
        token_count = cm.estimate_tokens(prompt)
        budget = cm.budget.system_prompt
        
        status = f"{Fore.GREEN}✓" if token_count <= budget else f"{Fore.RED}✗"
        print(f"\n{status} Strategy: {cm.strategy.value} (max_tokens={max_tokens})")
        print(f"  Prompt tokens: {token_count} / {budget} budget")
        print(f"  Prompt length: {len(prompt)} chars")
        print(f"  Preview: {prompt[:100]}...")


def test_schema_context():
    """Test schema context generation"""
    print_section("TEST 3: Schema Context Generation")
    
    # Sample schema
    sample_schema = {
        'tables': {
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'integer', 'primary_key': True, 'nullable': False},
                    {'name': 'username', 'type': 'varchar(50)', 'nullable': False, 'unique': True},
                    {'name': 'email', 'type': 'varchar(100)', 'nullable': False, 'unique': True},
                    {'name': 'created_at', 'type': 'timestamp', 'nullable': False},
                ],
                'foreign_keys': []
            },
            'orders': {
                'columns': [
                    {'name': 'id', 'type': 'integer', 'primary_key': True, 'nullable': False},
                    {'name': 'user_id', 'type': 'integer', 'nullable': False},
                    {'name': 'total', 'type': 'numeric(10,2)', 'nullable': False},
                    {'name': 'status', 'type': 'varchar(20)', 'nullable': False},
                ],
                'foreign_keys': [
                    {'column': 'user_id', 'foreign_table': 'users', 'foreign_column': 'id'}
                ]
            },
            'products': {
                'columns': [
                    {'name': 'id', 'type': 'integer', 'primary_key': True, 'nullable': False},
                    {'name': 'name', 'type': 'varchar(100)', 'nullable': False},
                    {'name': 'price', 'type': 'numeric(10,2)', 'nullable': False},
                    {'name': 'stock', 'type': 'integer', 'nullable': False},
                ],
                'foreign_keys': []
            }
        }
    }
    
    for max_tokens in [2000, 4000, 8000, 16000]:
        cm = ContextManager(max_tokens=max_tokens, strategy="auto")
        schema_context = cm.build_schema_context(schema=sample_schema, focused_tables=None)
        
        token_count = cm.estimate_tokens(schema_context)
        budget = cm.budget.schema
        
        status = f"{Fore.GREEN}✓" if token_count <= budget else f"{Fore.RED}✗"
        print(f"\n{status} Strategy: {cm.strategy.value} (max_tokens={max_tokens})")
        print(f"  Schema tokens: {token_count} / {budget} budget")
        print(f"  Schema length: {len(schema_context)} chars")
        
        # Show first few lines
        lines = schema_context.split('\n')[:5]
        print(f"  Preview:")
        for line in lines:
            print(f"    {line}")
        print(f"    ... ({len(schema_context.split(chr(10)))} total lines)")


def test_error_context():
    """Test error context generation"""
    print_section("TEST 4: Error Context Generation")
    
    error_msg = 'ERROR: column "users.username" does not exist\nLINE 1: SELECT users.username FROM user\n'
    analysis = {
        'hints': [
            'Table name is "user" but should be "users"',
            'Check table names in schema',
            'Use exact table names'
        ],
        'mentioned_tables': ['users', 'user']
    }
    previous_sql = 'SELECT users.username FROM user WHERE id = 1'
    
    for max_tokens in [2000, 4000, 8000, 16000]:
        cm = ContextManager(max_tokens=max_tokens, strategy="auto")
        error_context = cm.build_error_context(
            error_msg=error_msg,
            analysis=analysis,
            previous_sql=previous_sql,
            attempt_number=2
        )
        
        token_count = cm.estimate_tokens(error_context)
        budget = cm.budget.error_context
        
        status = f"{Fore.GREEN}✓" if token_count <= budget else f"{Fore.RED}✗"
        print(f"\n{status} Strategy: {cm.strategy.value} (max_tokens={max_tokens})")
        print(f"  Error context tokens: {token_count} / {budget} budget")
        print(f"  Preview: {error_context[:150]}...")


def test_token_estimation():
    """Test token estimation accuracy"""
    print_section("TEST 5: Token Estimation")
    
    test_texts = [
        ("Short text", "Hello world"),
        ("Medium text", "SELECT * FROM users WHERE id = 1" * 10),
        ("Long text", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50),
    ]
    
    cm = ContextManager(max_tokens=4000)
    
    for name, text in test_texts:
        estimated = cm.estimate_tokens(text)
        char_count = len(text)
        ratio = char_count / estimated if estimated > 0 else 0
        
        print(f"\n{name}:")
        print(f"  Characters: {char_count}")
        print(f"  Estimated tokens: {estimated}")
        print(f"  Chars per token: {ratio:.2f}")


def test_truncation():
    """Test text truncation to token limits"""
    print_section("TEST 6: Text Truncation")
    
    long_text = "This is a test sentence. " * 200  # ~1000 tokens
    
    cm = ContextManager(max_tokens=4000)
    
    for max_tokens in [50, 100, 200, 500]:
        truncated = cm.truncate_to_tokens(long_text, max_tokens)
        estimated = cm.estimate_tokens(truncated)
        
        status = f"{Fore.GREEN}✓" if estimated <= max_tokens else f"{Fore.RED}✗"
        print(f"\n{status} Truncate to {max_tokens} tokens:")
        print(f"  Original: {len(long_text)} chars ({cm.estimate_tokens(long_text)} tokens)")
        print(f"  Truncated: {len(truncated)} chars ({estimated} tokens)")
        print(f"  Within budget: {estimated <= max_tokens}")


def test_combined_context():
    """Test full context generation (system + schema + error)"""
    print_section("TEST 7: Combined Context (Real-world Scenario)")
    
    sample_schema = {
        'tables': {
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'integer', 'primary_key': True, 'nullable': False},
                    {'name': 'username', 'type': 'varchar(50)', 'nullable': False, 'unique': True},
                ],
                'foreign_keys': []
            }
        }
    }
    
    error_msg = 'ERROR: column does not exist'
    analysis = {'hints': ['Check column names']}
    
    for max_tokens in [2000, 4000, 8000]:
        cm = ContextManager(max_tokens=max_tokens, strategy="auto")
        
        system = cm.build_system_prompt()
        schema = cm.build_schema_context(sample_schema)
        error = cm.build_error_context(error_msg, analysis, attempt_number=2)
        
        total_tokens = (
            cm.estimate_tokens(system) +
            cm.estimate_tokens(schema) +
            cm.estimate_tokens(error)
        )
        
        status = f"{Fore.GREEN}✓" if total_tokens <= max_tokens else f"{Fore.RED}✗"
        print(f"\n{status} Strategy: {cm.strategy.value} (max_tokens={max_tokens})")
        print(f"  System prompt: {cm.estimate_tokens(system)} tokens")
        print(f"  Schema: {cm.estimate_tokens(schema)} tokens")
        print(f"  Error context: {cm.estimate_tokens(error)} tokens")
        print(f"  Total: {total_tokens} tokens")
        print(f"  Budget remaining: {max_tokens - total_tokens} tokens")
        print(f"  Within limit: {total_tokens <= max_tokens}")


def run_all_tests():
    """Run all tests"""
    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{Fore.YELLOW}Context Manager Test Suite")
    print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
    
    tests = [
        test_strategy_selection,
        test_system_prompts,
        test_schema_context,
        test_error_context,
        test_token_estimation,
        test_truncation,
        test_combined_context,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n{Fore.RED}✗ Test failed: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{Fore.YELLOW}All tests completed!")
    print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    run_all_tests()
