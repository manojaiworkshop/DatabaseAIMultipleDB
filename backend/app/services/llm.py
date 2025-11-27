"""
LLM service for SQL generation using different providers
"""
from openai import OpenAI
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate_sql(self, question: str, schema_context: str, 
                    conversation_history: Optional[List[Dict]] = None,
                    database_type: str = "postgresql") -> Dict[str, str]:
        """Generate SQL query from natural language question"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config['api_key']
        self.model = config['model']
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        # Create OpenAI client instance (v1.x API)
        self.client = OpenAI(api_key=self.api_key)
    
    def _get_database_specific_instructions(self, database_type: str) -> str:
        """Get database-specific SQL instructions"""
        if database_type == "oracle":
            return """ORACLE-SPECIFIC INSTRUCTIONS:
1. Use DUAL for testing queries (e.g., SELECT 1 FROM DUAL)
2. Use ROWNUM instead of LIMIT (e.g., WHERE ROWNUM <= 100)
3. String concatenation uses || operator
4. Date format: TO_DATE('2024-01-01', 'YYYY-MM-DD')
5. Use SYSDATE for current timestamp
6. Table metadata: SELECT * FROM user_tables, user_tab_columns
7. Schema objects are in ALL_TABLES, ALL_TAB_COLUMNS, DBA_USERS"""
        elif database_type == "mysql":
            return """MYSQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses CONCAT() function
3. Date format: STR_TO_DATE('2024-01-01', '%Y-%m-%d')
4. Use NOW() for current timestamp
5. Use SHOW TABLES, SHOW COLUMNS for metadata
6. Use backticks ` for identifiers with special chars
7. Auto-increment uses AUTO_INCREMENT keyword"""
        elif database_type == "sqlite":
            return """SQLITE-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || operator
3. Date/time: datetime('now'), date('now')
4. No stored procedures or triggers in basic SQLite
5. Use sqlite_master table for metadata
6. Type affinity: SQLite uses dynamic typing
7. No RIGHT JOIN or FULL OUTER JOIN support"""
        else:  # postgresql
            return """POSTGRESQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || or CONCAT()
3. Date format: TO_DATE('2024-01-01', 'YYYY-MM-DD')
4. Use NOW() or CURRENT_TIMESTAMP
5. Use information_schema for metadata
6. Arrays supported: ARRAY[1,2,3]
7. JSON/JSONB types supported"""
        
    def generate_sql(self, question: str, schema_context: str, 
                    conversation_history: Optional[List[Dict]] = None,
                    database_type: str = "postgresql") -> Dict[str, str]:
        """Generate SQL using OpenAI"""
        try:
            db_name = database_type.upper() if database_type else "SQL"
            db_instructions = self._get_database_specific_instructions(database_type)
            
            system_prompt = f"""You are a {db_name} SQL query generator. Your job is to convert natural language questions into valid {db_name} queries.

Database Schema:
{schema_context}

{db_instructions}

CRITICAL INSTRUCTIONS:
1. Generate ONLY valid {db_name} SQL queries
2. Return response in this EXACT JSON format: {{"sql": "YOUR_SQL_HERE", "explanation": "brief explanation"}}
3. The "sql" field must contain ONLY executable SQL - no explanatory text
4. Use ONLY tables and columns from the schema above
5. Add appropriate row limiting for SELECT queries when appropriate

EXAMPLE RESPONSES:
Question: "How many users are there?"
Response: {{"sql": "SELECT COUNT(*) FROM users;", "explanation": "Counts all users"}}

Question: "Show all products"
Response: {{"sql": "SELECT * FROM products LIMIT 100;", "explanation": "Lists all products"}}"""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": question})
            
            # Use the client instance for API calls (v1.x)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            logger.info(f"Raw OpenAI response: {content[:200]}...")  # Log first 200 chars
            
            # Try to extract JSON from content
            try:
                # First try direct parsing
                result = json.loads(content)
                if 'sql' not in result:
                    raise ValueError("Response missing 'sql' field")
                return result
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from OpenAI: {e}")
                # Try to find JSON object in the text
                import re
                json_match = re.search(r'\{[^}]*"sql"[^}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if 'sql' in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: extract SQL from code blocks
                sql = self._extract_sql(content)
                if not sql or len(sql) == 0:
                    raise ValueError(f"Failed to extract valid SQL from OpenAI response: {content[:200]}")
                return {"sql": sql, "explanation": ""}
                
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def _extract_sql(self, content: str) -> str:
        """Extract SQL from content"""
        import re
        
        # Skip explanatory text
        if any(x in content.upper() for x in ['BASED ON', 'HERE ARE', 'THERE ARE', 'THE FOLLOWING']):
            # Try to find actual SQL after explanation
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']
            for keyword in sql_keywords:
                if keyword in content.upper():
                    # Extract from keyword onwards
                    idx = content.upper().find(keyword)
                    content = content[idx:]
                    break
        
        # Remove markdown code blocks
        if "```sql" in content:
            content = content.split("```sql")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # Clean up and return
        sql = content.strip()
        
        # If still contains explanatory text at start, try to extract SQL
        if not any(sql.upper().startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']):
            return ""
        
        return sql


class VLLMProvider(BaseLLMProvider):
    """vLLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_url = config['api_url']
        self.model = config['model']
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
    
    def _get_database_specific_instructions(self, database_type: str) -> str:
        """Get database-specific SQL instructions (shared with OpenAI)"""
        if database_type == "oracle":
            return """ORACLE-SPECIFIC INSTRUCTIONS:
1. Use DUAL for testing queries (e.g., SELECT 1 FROM DUAL)
2. Use ROWNUM instead of LIMIT (e.g., WHERE ROWNUM <= 100)
3. String concatenation uses || operator
4. Date format: TO_DATE('2024-01-01', 'YYYY-MM-DD')
5. Use SYSDATE for current timestamp"""
        elif database_type == "mysql":
            return """MYSQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses CONCAT() function
3. Date format: STR_TO_DATE('2024-01-01', '%Y-%m-%d')
4. Use NOW() for current timestamp
5. Use backticks ` for identifiers with special chars"""
        elif database_type == "sqlite":
            return """SQLITE-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || operator
3. Date/time: datetime('now'), date('now')
4. Use sqlite_master table for metadata"""
        else:  # postgresql
            return """POSTGRESQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || or CONCAT()
3. Use information_schema for metadata"""
        
    def generate_sql(self, question: str, schema_context: str, 
                    conversation_history: Optional[List[Dict]] = None,
                    database_type: str = "postgresql") -> Dict[str, str]:
        """Generate SQL using vLLM"""
        try:
            db_name = database_type.upper() if database_type else "SQL"
            db_instructions = self._get_database_specific_instructions(database_type)
            
            system_prompt = f"""You are a {db_name} SQL query generator. Your job is to convert natural language questions into valid {db_name} queries.

Database Schema:
{schema_context}

{db_instructions}

CRITICAL INSTRUCTIONS:
1. Generate ONLY valid {db_name} SQL queries
2. Return response in this EXACT JSON format: {{"sql": "YOUR_SQL_HERE", "explanation": "brief explanation"}}
3. The "sql" field must contain ONLY executable SQL - no explanatory text
4. Use ONLY tables and columns from the schema above"""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": question})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            logger.info(f"Sending request to vLLM with {len(messages)} messages, total chars: {sum(len(str(m)) for m in messages)}")
            
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            # Check for errors
            if response.status_code != 200:
                error_detail = response.text[:500]  # Get first 500 chars of error
                logger.error(f"vLLM API error {response.status_code}: {error_detail}")
                raise Exception(f"vLLM API returned {response.status_code}. This usually means the request is too large or malformed. Try reducing context size.")
            
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            logger.info(f"Raw vLLM response: {content[:200]}...")  # Log first 200 chars
            
            # Try to extract JSON from content
            try:
                # First try direct parsing
                parsed = json.loads(content)
                if 'sql' not in parsed:
                    raise ValueError("Response missing 'sql' field")
                return parsed
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from vLLM: {e}")
                # Try to find JSON object in the text
                import re
                json_match = re.search(r'\{[^}]*"sql"[^}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if 'sql' in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: extract SQL from code blocks
                sql = self._extract_sql(content)
                if not sql or len(sql) == 0:
                    raise ValueError(f"Failed to extract valid SQL from vLLM response: {content[:200]}")
                return {"sql": sql, "explanation": ""}
                
        except Exception as e:
            logger.error(f"vLLM generation failed: {e}")
            raise
    
    def _extract_sql(self, content: str) -> str:
        """Extract SQL from content"""
        if "```sql" in content:
            content = content.split("```sql")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return content.strip()


class OllamaProvider(BaseLLMProvider):
    """Ollama provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_url = config['api_url']
        self.model = config['model']
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.stream = config.get('stream', False)
    
    def _get_database_specific_instructions(self, database_type: str) -> str:
        """Get database-specific SQL instructions"""
        if database_type == "oracle":
            return """ORACLE-SPECIFIC INSTRUCTIONS:
1. Use DUAL for testing queries (e.g., SELECT 1 FROM DUAL)
2. Use ROWNUM instead of LIMIT (e.g., WHERE ROWNUM <= 100)
3. String concatenation uses || operator
4. Date format: TO_DATE('2024-01-01', 'YYYY-MM-DD')
5. Use SYSDATE for current timestamp"""
        elif database_type == "mysql":
            return """MYSQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses CONCAT() function
3. Date format: STR_TO_DATE('2024-01-01', '%Y-%m-%d')
4. Use NOW() for current timestamp
5. Use backticks ` for identifiers with special chars"""
        elif database_type == "sqlite":
            return """SQLITE-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || operator
3. Date/time: datetime('now'), date('now')
4. Use sqlite_master table for metadata"""
        else:  # postgresql
            return """POSTGRESQL-SPECIFIC INSTRUCTIONS:
1. Use LIMIT for row limiting (e.g., LIMIT 100)
2. String concatenation uses || or CONCAT()
3. Use information_schema for metadata"""
        
    def generate_sql(self, question: str, schema_context: str, 
                    conversation_history: Optional[List[Dict]] = None,
                    database_type: str = "postgresql") -> Dict[str, str]:
        """Generate SQL using Ollama"""
        try:
            db_name = database_type.upper() if database_type else "SQL"
            db_instructions = self._get_database_specific_instructions(database_type)
            
            system_prompt = f"""You are a {db_name} SQL query generator. Your ONLY job is to generate valid {db_name} SQL queries.

Database Schema:
{schema_context}

{db_instructions}

CRITICAL RULES:
1. Generate ONLY {db_name} SQL queries - NO code in other languages (no PHP, Python, JavaScript, etc.)
2. Return response ONLY in this JSON format: {{"sql": "YOUR_SQL_QUERY_HERE", "explanation": "brief explanation"}}
3. Use ONLY the tables and columns shown in the schema above
4. Use proper {db_name} syntax
5. Add appropriate row limiting for SELECT queries
6. For data modification: Only if explicitly requested in the question

RESPOND WITH PURE SQL ONLY - NO OTHER CODE OR EXPLANATIONS OUTSIDE THE JSON FORMAT."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": question})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": self.stream,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['message']['content'].strip()
            
            logger.info(f"Raw Ollama response: {content[:200]}...")  # Log first 200 chars
            
            # Try to extract JSON from content
            try:
                # First try direct parsing
                parsed = json.loads(content)
                if 'sql' not in parsed:
                    raise ValueError("Response missing 'sql' field")
                return parsed
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from Ollama: {e}")
                # Try to find JSON object in the text
                import re
                json_match = re.search(r'\{[^}]*"sql"[^}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if 'sql' in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: extract SQL from code blocks
                sql = self._extract_sql_ollama(content)
                if not sql or len(sql.strip()) == 0:
                    raise ValueError(f"Failed to extract valid SQL from Ollama response: {content[:200]}")
                return {"sql": sql, "explanation": ""}
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _extract_sql_ollama(self, content: str) -> str:
        """Extract SQL from content, filtering out non-SQL code"""
        import re
        
        # First try to find SQL code blocks
        if "```sql" in content:
            sql_match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
            if sql_match:
                return sql_match.group(1).strip()
        
        # Try to find any code block, but filter out non-SQL languages
        code_blocks = re.findall(r'```(\w+)?\s*(.*?)\s*```', content, re.DOTALL)
        for lang, code in code_blocks:
            # Skip non-SQL languages
            if lang and lang.lower() in ['php', 'python', 'javascript', 'java', 'ruby', 'go']:
                continue
            # If it's a SQL-like block or no language specified, use it
            if not lang or lang.lower() in ['sql', 'postgresql', 'pgsql']:
                return code.strip()
        
        # Look for SQL keywords to extract SQL statements
        sql_keywords = ['SELECT', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'WITH']
        lines = content.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line_upper = line.strip().upper()
            # Skip lines that are clearly not SQL
            if any(x in line_upper for x in ['BASED ON', 'HERE ARE', 'THERE ARE', 'THE FOLLOWING']):
                continue
            
            # Check if line starts with SQL keyword
            if any(line_upper.startswith(kw) for kw in sql_keywords):
                in_sql = True
                sql_lines.append(line)
            elif in_sql:
                # Continue collecting lines if we're in SQL
                if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('#') and not any(c.isalpha() and line.strip()[0].isdigit() for c in line):
                    # Check if it looks like SQL continuation (contains keywords, operators, etc.)
                    if any(kw in line_upper for kw in ['FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'AND', 'OR', ';']) or not line.strip()[0].isalpha():
                        sql_lines.append(line)
                    else:
                        # Stop if it doesn't look like SQL
                        break
                elif not line.strip() and sql_lines:
                    # Empty line after SQL - might be end
                    break
        
        if sql_lines:
            sql = '\n'.join(sql_lines).strip()
            # Remove trailing semicolon and anything after
            if ';' in sql:
                sql = sql.split(';')[0] + ';'
            return sql
        
        # Last resort: return empty to trigger error
        return ""


class LLMService:
    """Main LLM service that manages different providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_provider = config['llm']['provider']
        self.providers = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all LLM providers"""
        if 'openai' in self.config:
            self.providers['openai'] = OpenAIProvider(self.config['openai'])
        
        if 'vllm' in self.config:
            self.providers['vllm'] = VLLMProvider(self.config['vllm'])
        
        if 'ollama' in self.config:
            self.providers['ollama'] = OllamaProvider(self.config['ollama'])
    
    def reload_config(self, config: Dict[str, Any]):
        """Reload configuration and reinitialize providers"""
        self.config = config
        self.current_provider = config['llm']['provider']
        self.providers = {}
        self._initialize_providers()
        logger.info(f"LLM service reloaded with provider: {self.current_provider}")
    
    def set_provider(self, provider_name: str):
        """Switch LLM provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not configured")
        self.current_provider = provider_name
        logger.info(f"Switched to provider: {provider_name}")
    
    def generate_sql(self, question: str, schema_context: str, 
                    conversation_history: Optional[List[Dict]] = None,
                    database_type: str = "postgresql") -> Dict[str, str]:
        """Generate SQL using current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            raise ValueError(f"Provider {self.current_provider} not available")
        
        logger.info(f"Generating SQL using {self.current_provider} for {database_type}")
        return provider.generate_sql(question, schema_context, conversation_history, database_type)
    
    def generate_structured(self, messages: List[Dict], max_tokens: int = 1024) -> Any:
        """
        Generate structured JSON response from LLM.
        Used for ontology generation and other structured outputs.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON object (dict or list)
            
        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        import re
        
        provider = self.providers.get(self.current_provider)
        if not provider:
            raise ValueError(f"Provider {self.current_provider} not available")
        
        logger.info(f"Generating structured response using {self.current_provider}")
        
        try:
            # Make the request based on provider type
            if self.current_provider == 'openai':
                # Use the client instance (v1.x API)
                response = provider.client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    temperature=provider.temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content.strip()
                
            elif self.current_provider == 'vllm':
                payload = {
                    "model": provider.model,
                    "messages": messages,
                    "temperature": provider.temperature,
                    "max_tokens": max_tokens
                }
                response = requests.post(provider.api_url, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
            elif self.current_provider == 'ollama':
                payload = {
                    "model": provider.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": provider.temperature,
                        "num_predict": max_tokens
                    }
                }
                response = requests.post(provider.api_url, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                content = result['message']['content'].strip()
            else:
                raise ValueError(f"Unknown provider: {self.current_provider}")
            
            logger.info(f"Raw structured response: {content[:200]}...")
            
            # Strategy 1: Try direct JSON parse
            try:
                parsed = json.loads(content)
                logger.info(f"✅ Direct JSON parse successful: {type(parsed).__name__}")
                return parsed
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Try to extract fenced JSON block (```json ... ```)
            fenced_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```', content, re.IGNORECASE)
            if fenced_match:
                try:
                    parsed = json.loads(fenced_match.group(1))
                    logger.info(f"✅ Fenced JSON parse successful: {type(parsed).__name__}")
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Strategy 3: Try to find first JSON object or array
            json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    logger.info(f"✅ Regex JSON parse successful: {type(parsed).__name__}")
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Failed all strategies
            logger.error(f"Failed to parse structured response. Content: {content[:500]}")
            raise ValueError(f"Failed to parse JSON from LLM response: {content[:500]}")
            
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise
