"""
Intelligent Context Manager for Dynamic Token Budget Allocation

This module handles context generation based on available token budget.
It automatically adjusts verbosity levels to stay within token limits.

Context Strategies:
- CONCISE: < 3000 tokens - Minimal schema, compact errors
- SEMI_EXPANDED: 3000-6000 tokens - Key tables with samples, moderate detail
- EXPANDED: 6000-10000 tokens - Full schema with relationships, detailed errors
- LARGE: > 10000 tokens - Complete context with examples and documentation

Author: DatabaseAI Team
Date: October 2025
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ContextStrategy(Enum):
    """Context verbosity levels"""
    CONCISE = "concise"           # < 3000 tokens
    SEMI_EXPANDED = "semi"         # 3000-6000 tokens
    EXPANDED = "expanded"          # 6000-10000 tokens
    LARGE = "large"                # > 10000 tokens


class TokenBudget:
    """Token budget allocations for different context parts"""
    
    def __init__(self, max_tokens: int, strategy: ContextStrategy):
        self.max_tokens = max_tokens
        self.strategy = strategy
        self._calculate_budgets()
    
    def _calculate_budgets(self):
        """Calculate token budgets for each context part"""
        if self.strategy == ContextStrategy.CONCISE:
            # Ultra-compact for small models (< 3000)
            self.system_prompt = int(self.max_tokens * 0.15)  # 15%
            self.schema = int(self.max_tokens * 0.40)         # 40%
            self.conversation = int(self.max_tokens * 0.20)   # 20%
            self.error_context = int(self.max_tokens * 0.15)  # 15%
            self.reserved = int(self.max_tokens * 0.10)       # 10% buffer
            
        elif self.strategy == ContextStrategy.SEMI_EXPANDED:
            # Balanced for medium models (3000-6000)
            self.system_prompt = int(self.max_tokens * 0.12)  # 12%
            self.schema = int(self.max_tokens * 0.45)         # 45%
            self.conversation = int(self.max_tokens * 0.20)   # 20%
            self.error_context = int(self.max_tokens * 0.13)  # 13%
            self.reserved = int(self.max_tokens * 0.10)       # 10% buffer
            
        elif self.strategy == ContextStrategy.EXPANDED:
            # Detailed for large models (6000-10000)
            self.system_prompt = int(self.max_tokens * 0.10)  # 10%
            self.schema = int(self.max_tokens * 0.50)         # 50%
            self.conversation = int(self.max_tokens * 0.20)   # 20%
            self.error_context = int(self.max_tokens * 0.10)  # 10%
            self.reserved = int(self.max_tokens * 0.10)       # 10% buffer
            
        else:  # LARGE
            # Comprehensive for very large models (> 10000)
            self.system_prompt = int(self.max_tokens * 0.08)  # 8%
            self.schema = int(self.max_tokens * 0.55)         # 55%
            self.conversation = int(self.max_tokens * 0.20)   # 20%
            self.error_context = int(self.max_tokens * 0.10)  # 10%
            self.reserved = int(self.max_tokens * 0.07)       # 7% buffer


class ContextManager:
    """
    Intelligent context manager that adapts to token limits
    
    Features:
    - Automatic strategy selection based on max_tokens
    - Dynamic schema truncation to fit budget
    - Smart error context summarization
    - Token counting and budget tracking
    """
    
    def __init__(self, max_tokens: int, strategy: Optional[str] = "auto"):
        """
        Initialize context manager
        
        Args:
            max_tokens: Maximum tokens allowed in context
            strategy: 'auto', 'concise', 'semi', 'expanded', or 'large'
        """
        self.max_tokens = max_tokens
        
        if strategy == "auto":
            self.strategy = self._determine_strategy(max_tokens)
        else:
            self.strategy = ContextStrategy(strategy)
        
        self.budget = TokenBudget(max_tokens, self.strategy)
        
        logger.info(f"ContextManager initialized: max_tokens={max_tokens}, strategy={self.strategy.value}")
        logger.info(f"Budget allocation: schema={self.budget.schema}, "
                   f"conversation={self.budget.conversation}, "
                   f"error={self.budget.error_context}")
    
    def _determine_strategy(self, max_tokens: int) -> ContextStrategy:
        """Automatically determine best strategy based on token limit"""
        if max_tokens < 3000:
            return ContextStrategy.CONCISE
        elif max_tokens < 6000:
            return ContextStrategy.SEMI_EXPANDED
        elif max_tokens < 10000:
            return ContextStrategy.EXPANDED
        else:
            return ContextStrategy.LARGE
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Uses simple heuristic: ~4 characters per token
        This is conservative and works well across models
        """
        if not text:
            return 0
        # Average: 4 chars per token (includes spaces, punctuation)
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token budget"""
        estimated = self.estimate_tokens(text)
        
        if estimated <= max_tokens:
            return text
        
        # Calculate character limit
        char_limit = max_tokens * 4
        
        if len(text) <= char_limit:
            return text
        
        # Truncate with ellipsis
        return text[:char_limit - 20] + "\n... (truncated)"
    
    def build_system_prompt(self) -> str:
        """Build system prompt based on strategy"""
        
        if self.strategy == ContextStrategy.CONCISE:
            prompt = """You are a SQL expert. Generate ONLY valid SQL queries.
Rules:
1. Return ONLY the SQL query, no explanations
2. Use exact table/column names from schema
3. Use proper JOIN syntax
4. Fix errors from previous attempts"""
        
        elif self.strategy == ContextStrategy.SEMI_EXPANDED:
            prompt = """You are a SQL query expert. Generate accurate SQL queries based on natural language questions.

Key Rules:
1. Return ONLY the SQL query without any explanations or markdown
2. Use EXACT table and column names from the provided schema
3. Use proper JOIN syntax with explicit conditions
4. Handle NULL values appropriately
5. If previous attempts failed, analyze the error and fix the issue
6. For ambiguous questions, make reasonable assumptions based on schema"""
        
        elif self.strategy == ContextStrategy.EXPANDED:
            prompt = """You are an expert SQL query generator with deep knowledge of PostgreSQL.

Your Task:
Generate precise, optimized SQL queries that answer the user's natural language questions.

Core Rules:
1. Output Format: Return ONLY the SQL query without explanations, comments, or markdown
2. Schema Accuracy: Use EXACT table and column names from the provided database schema
3. JOIN Operations: Use explicit JOIN syntax with clear ON conditions
4. Data Types: Respect column data types and use appropriate type casting when needed
5. Error Recovery: If previous attempts failed, carefully analyze the error message and fix the root cause
6. Ambiguity Handling: Make reasonable assumptions based on schema relationships
7. Optimization: Use efficient query patterns (avoid SELECT *, use indexes when possible)

Special Considerations:
- Handle NULL values with COALESCE or IS NULL checks
- Use appropriate aggregate functions (COUNT, SUM, AVG, etc.)
- Apply proper filtering with WHERE clauses
- Sort results logically with ORDER BY when relevant"""
        
        else:  # LARGE
            prompt = """You are an expert SQL query generator with comprehensive knowledge of PostgreSQL and database best practices.

Mission:
Transform natural language questions into precise, efficient, and correct SQL queries that execute flawlessly.

Comprehensive Rules:

1. Output Format:
   - Return ONLY the executable SQL query
   - NO explanations, comments, markdown formatting, or meta-commentary
   - The query should be ready to execute as-is

2. Schema Adherence:
   - Use EXACT table names and column names from the provided schema
   - Never assume columns exist - verify against schema
   - Respect foreign key relationships and table relationships

3. JOIN Operations:
   - Use explicit JOIN syntax (INNER JOIN, LEFT JOIN, etc.)
   - Always specify ON conditions clearly
   - Consider the relationship cardinality (one-to-many, many-to-many)

4. Data Types & Casting:
   - Respect column data types (integer, varchar, timestamp, etc.)
   - Use explicit type casting when comparing different types
   - Example: column_name::INTEGER or CAST(column_name AS INTEGER)

5. Error Recovery:
   - If previous attempts failed, analyze the error message carefully
   - Common issues: wrong column names, type mismatches, missing JOINs
   - Fix the root cause, don't just try variations

6. Query Optimization:
   - Avoid SELECT * in production queries (specify columns)
   - Use indexes when available
   - Filter early with WHERE clauses
   - Use EXISTS instead of IN for subqueries when appropriate

7. NULL Handling:
   - Use IS NULL / IS NOT NULL for NULL checks
   - Use COALESCE for default values
   - Be aware that NULL != NULL in comparisons

8. Aggregation:
   - Use GROUP BY with aggregate functions (COUNT, SUM, AVG, etc.)
   - Apply HAVING for filtering grouped results
   - Use DISTINCT when appropriate

9. Sorting & Limiting:
   - Add ORDER BY for meaningful result ordering
   - Use LIMIT for pagination or top-N queries
   - Consider DESC for descending order

10. Ambiguity Resolution:
    - If question is ambiguous, make reasonable assumptions
    - Prefer common patterns (recent data, active records)
    - Document assumptions in the query structure"""
        
        # Truncate to budget
        return self.truncate_to_tokens(prompt, self.budget.system_prompt)
    
    def build_schema_context(self, schema: Dict, 
                            focused_tables: Optional[List[str]] = None,
                            include_samples: bool = False) -> str:
        """
        Build schema context based on strategy and token budget
        
        Args:
            schema: Full database schema dictionary
            focused_tables: Tables to prioritize (for error recovery)
            include_samples: Whether to include sample data
        
        Returns:
            Formatted schema string within token budget
        """
        if not schema or 'tables' not in schema:
            return "No schema available."
        
        tables = schema['tables']
        
        if self.strategy == ContextStrategy.CONCISE:
            # Minimal schema: just table and column names
            return self._build_concise_schema(tables, focused_tables)
        
        elif self.strategy == ContextStrategy.SEMI_EXPANDED:
            # Include data types and primary keys
            return self._build_semi_schema(tables, focused_tables)
        
        elif self.strategy == ContextStrategy.EXPANDED:
            # Include relationships and constraints
            return self._build_expanded_schema(tables, focused_tables, include_samples)
        
        else:  # LARGE
            # Full schema with samples and documentation
            return self._build_large_schema(tables, focused_tables, include_samples)
    
    def _build_concise_schema(self, tables: Dict, focused_tables: Optional[List[str]]) -> str:
        """Build ultra-compact schema"""
        lines = ["📊 DATABASE SCHEMA:\n"]
        
        # Prioritize focused tables
        table_list = focused_tables if focused_tables else list(tables.keys())
        
        # Limit tables if needed
        max_tables = 15 if self.strategy == ContextStrategy.CONCISE else 30
        
        for table_name in table_list[:max_tables]:
            if table_name not in tables:
                continue
            
            columns = tables[table_name].get('columns', [])
            col_names = [col['name'] for col in columns[:10]]  # Limit columns
            
            lines.append(f"• {table_name}: {', '.join(col_names)}")
        
        result = "\n".join(lines)
        return self.truncate_to_tokens(result, self.budget.schema)
    
    def _build_semi_schema(self, tables: Dict, focused_tables: Optional[List[str]]) -> str:
        """Build semi-expanded schema with types"""
        lines = ["📊 DATABASE SCHEMA:\n"]
        
        table_list = focused_tables if focused_tables else list(tables.keys())
        max_tables = 20
        
        for table_name in table_list[:max_tables]:
            if table_name not in tables:
                continue
            
            columns = tables[table_name].get('columns', [])
            lines.append(f"\nTable: {table_name}")
            
            for col in columns[:15]:  # Limit columns per table
                col_info = f"  - {col['name']} ({col['type']})"
                if col.get('primary_key'):
                    col_info += " [PK]"
                if not col.get('nullable', True):
                    col_info += " NOT NULL"
                lines.append(col_info)
        
        result = "\n".join(lines)
        return self.truncate_to_tokens(result, self.budget.schema)
    
    def _build_expanded_schema(self, tables: Dict, focused_tables: Optional[List[str]], 
                               include_samples: bool) -> str:
        """Build expanded schema with relationships"""
        lines = ["📊 DATABASE SCHEMA:\n"]
        
        table_list = focused_tables if focused_tables else list(tables.keys())
        max_tables = 25
        
        for table_name in table_list[:max_tables]:
            if table_name not in tables:
                continue
            
            table_info = tables[table_name]
            columns = table_info.get('columns', [])
            
            lines.append(f"\n{'='*50}")
            lines.append(f"Table: {table_name}")
            lines.append(f"{'='*50}")
            
            # Columns
            lines.append("Columns:")
            for col in columns:
                col_info = f"  • {col['name']}: {col['type']}"
                
                flags = []
                if col.get('primary_key'):
                    flags.append("PRIMARY KEY")
                if not col.get('nullable', True):
                    flags.append("NOT NULL")
                if col.get('unique'):
                    flags.append("UNIQUE")
                
                if flags:
                    col_info += f" [{', '.join(flags)}]"
                
                lines.append(col_info)
            
            # Foreign Keys
            foreign_keys = table_info.get('foreign_keys', [])
            if foreign_keys:
                lines.append("\nRelationships:")
                for fk in foreign_keys:
                    lines.append(f"  → {fk['column']} references {fk['foreign_table']}.{fk['foreign_column']}")
            
            # Sample data if requested
            if include_samples and 'sample_data' in table_info:
                lines.append("\nSample Data (first 2 rows):")
                for row in table_info['sample_data'][:2]:
                    lines.append(f"  {row}")
        
        result = "\n".join(lines)
        return self.truncate_to_tokens(result, self.budget.schema)
    
    def _build_large_schema(self, tables: Dict, focused_tables: Optional[List[str]], 
                           include_samples: bool) -> str:
        """Build comprehensive schema with all details"""
        lines = ["📊 COMPREHENSIVE DATABASE SCHEMA:\n"]
        
        # Include all tables for large context
        table_list = focused_tables if focused_tables else list(tables.keys())
        
        for table_name in table_list:
            if table_name not in tables:
                continue
            
            table_info = tables[table_name]
            columns = table_info.get('columns', [])
            
            lines.append(f"\n{'='*60}")
            lines.append(f"TABLE: {table_name}")
            lines.append(f"{'='*60}")
            
            # Row count if available
            if 'row_count' in table_info:
                lines.append(f"Row Count: {table_info['row_count']}")
            
            # Columns with full details
            lines.append("\nCOLUMNS:")
            for col in columns:
                col_detail = f"  • {col['name']}"
                col_detail += f"\n    Type: {col['type']}"
                
                if col.get('primary_key'):
                    col_detail += "\n    Constraint: PRIMARY KEY"
                if not col.get('nullable', True):
                    col_detail += "\n    Constraint: NOT NULL"
                if col.get('unique'):
                    col_detail += "\n    Constraint: UNIQUE"
                if 'default' in col:
                    col_detail += f"\n    Default: {col['default']}"
                
                lines.append(col_detail)
            
            # Foreign Keys
            foreign_keys = table_info.get('foreign_keys', [])
            if foreign_keys:
                lines.append("\nFOREIGN KEY RELATIONSHIPS:")
                for fk in foreign_keys:
                    lines.append(f"  • {fk['column']} → {fk['foreign_table']}.{fk['foreign_column']}")
                    if 'on_delete' in fk:
                        lines.append(f"    On Delete: {fk['on_delete']}")
            
            # Indexes
            if 'indexes' in table_info:
                lines.append("\nINDEXES:")
                for idx in table_info['indexes']:
                    lines.append(f"  • {idx['name']}: {idx.get('columns', [])}")
            
            # Sample data
            if include_samples and 'sample_data' in table_info:
                lines.append("\nSAMPLE DATA (first 3 rows):")
                for i, row in enumerate(table_info['sample_data'][:3], 1):
                    lines.append(f"  Row {i}: {row}")
        
        result = "\n".join(lines)
        return self.truncate_to_tokens(result, self.budget.schema)
    
    def build_error_context(self, error_msg: str, 
                           analysis: Optional[Dict] = None,
                           previous_sql: Optional[str] = None,
                           attempt_number: int = 1) -> str:
        """
        Build error context for retry attempts
        
        Args:
            error_msg: The error message from database
            analysis: Analyzed error with hints and suggestions
            previous_sql: The SQL that failed
            attempt_number: Current retry attempt number
        
        Returns:
            Formatted error context within token budget
        """
        lines = [f"\n⚠️ ATTEMPT #{attempt_number} - Previous attempt failed. Fix the error:\n"]
        
        if self.strategy == ContextStrategy.CONCISE:
            # Minimal error info
            lines.append(f"Error: {error_msg[:200]}")
            if analysis and 'hints' in analysis:
                lines.append(f"Fix: {analysis['hints'][0] if analysis['hints'] else 'Check schema'}")
        
        elif self.strategy == ContextStrategy.SEMI_EXPANDED:
            # Include error + hints
            lines.append(f"Error Message:\n{error_msg[:400]}")
            
            if previous_sql:
                lines.append(f"\nFailed SQL:\n{previous_sql[:300]}")
            
            if analysis:
                if analysis.get('hints'):
                    lines.append("\n💡 Hints:")
                    for hint in analysis['hints'][:2]:
                        lines.append(f"  • {hint}")
        
        elif self.strategy in [ContextStrategy.EXPANDED, ContextStrategy.LARGE]:
            # Full error context
            lines.append(f"Error Message:\n{error_msg}")
            
            if previous_sql:
                lines.append(f"\nFailed SQL Query:\n{previous_sql}")
            
            if analysis:
                if analysis.get('error_type'):
                    lines.append(f"\nError Type: {analysis['error_type']}")
                
                if analysis.get('mentioned_tables'):
                    lines.append(f"\nTables Mentioned: {', '.join(analysis['mentioned_tables'])}")
                
                if analysis.get('mentioned_columns'):
                    lines.append(f"Columns Mentioned: {', '.join(analysis['mentioned_columns'])}")
                
                if analysis.get('hints'):
                    lines.append("\n💡 Suggestions:")
                    for hint in analysis['hints']:
                        lines.append(f"  • {hint}")
                
                if analysis.get('focused_schema'):
                    lines.append(f"\n📋 Relevant Schema:\n{analysis['focused_schema']}")
        
        result = "\n".join(lines)
        return self.truncate_to_tokens(result, self.budget.error_context)
    
    def build_conversation_history(self, messages: List[Dict]) -> str:
        """
        Build conversation history within token budget
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Formatted conversation within budget
        """
        if not messages:
            return ""
        
        lines = []
        total_tokens = 0
        
        # Process messages in reverse (most recent first)
        for msg in reversed(messages[-10:]):  # Last 10 messages max
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Format message
            msg_text = f"{role.upper()}: {content}"
            msg_tokens = self.estimate_tokens(msg_text)
            
            if total_tokens + msg_tokens > self.budget.conversation:
                break
            
            lines.insert(0, msg_text)
            total_tokens += msg_tokens
        
        if lines:
            return "\n\nConversation History:\n" + "\n".join(lines)
        return ""
    
    def get_context_stats(self) -> Dict:
        """Get statistics about current context configuration"""
        return {
            "max_tokens": self.max_tokens,
            "strategy": self.strategy.value,
            "budgets": {
                "system_prompt": self.budget.system_prompt,
                "schema": self.budget.schema,
                "conversation": self.budget.conversation,
                "error_context": self.budget.error_context,
                "reserved": self.budget.reserved
            },
            "total_allocated": (
                self.budget.system_prompt + 
                self.budget.schema + 
                self.budget.conversation + 
                self.budget.error_context + 
                self.budget.reserved
            )
        }


def create_context_manager(config: Dict) -> ContextManager:
    """
    Factory function to create ContextManager from config
    
    Args:
        config: Configuration dictionary with llm settings
    
    Returns:
        Configured ContextManager instance
    """
    max_tokens = config.get('llm', {}).get('max_tokens', 4000)
    strategy = config.get('llm', {}).get('context_strategy', 'auto')
    
    return ContextManager(max_tokens=max_tokens, strategy=strategy)
