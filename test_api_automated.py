"""
Automated API Testing Script for DatabaseAI
Reads queries from TEST_QUERIES.md and tests the API automatically
"""

import requests
import json
import time
import re
import yaml
from typing import List, Dict, Tuple
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama for colored output
init(autoreset=True)

# Load database configuration from config.yml
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# Configuration
API_BASE_URL = "http://localhost:8088/api/v1"
DB_CONFIG = {
    "host": db_config['host'],
    "port": db_config['port'],
    "database": db_config['database'],
    "username": db_config['user'],
    "password": db_config['password'],
    "use_docker": False,
    "docker_container": ""
}

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print("\n" + "=" * 100)
        print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(100)}")
        print("=" * 100)
    
    def print_subheader(self, text: str):
        """Print a formatted subheader"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'─' * 100}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{text}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{'─' * 100}")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {text}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Fore.RED}✗ {text}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ {text}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠ {text}")
    
    def connect_database(self) -> bool:
        """Connect to the database"""
        self.print_subheader("Step 1: Connecting to Database")
        
        try:
            response = self.session.post(
                f"{self.base_url}/database/connect",
                json=DB_CONFIG,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success(f"Connected to database: {data['database_info']['database']}")
                    self.print_info(f"Tables: {data['database_info']['table_count']}")
                    return True
                else:
                    self.print_error(f"Connection failed: {data.get('message')}")
                    return False
            else:
                self.print_error(f"API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Connection error: {e}")
            return False
    
    def test_query(self, query_num: int, query_text: str, max_retries: int = 3) -> Dict:
        """Test a single query"""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json={
                    "question": query_text,
                    "max_retries": max_retries
                },
                timeout=120  # 2 minutes timeout for complex queries
            )
            
            elapsed_time = time.time() - start_time
            
            result = {
                "query_num": query_num,
                "query_text": query_text,
                "status_code": response.status_code,
                "elapsed_time": elapsed_time,
                "success": False,
                "row_count": 0,
                "sql_query": "",
                "error": None,
                "retry_count": 0
            }
            
            if response.status_code == 200:
                data = response.json()
                result["success"] = True
                result["row_count"] = data.get("row_count", 0)
                result["sql_query"] = data.get("sql_query", "")
                result["retry_count"] = data.get("retry_count", 0)
                result["execution_time"] = data.get("execution_time", 0)
            else:
                result["error"] = response.text
                
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                "query_num": query_num,
                "query_text": query_text,
                "status_code": 0,
                "elapsed_time": elapsed_time,
                "success": False,
                "row_count": 0,
                "sql_query": "",
                "error": str(e),
                "retry_count": 0
            }
    
    def parse_queries_from_md(self, file_path: str) -> List[Tuple[int, str]]:
        """Parse queries from TEST_QUERIES.md file"""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract queries - look for numbered patterns like "1. ", "2. ", etc.
            # or "**Query 1:**", etc.
            
            # Pattern 1: Numbered list "1. Query text"
            pattern1 = r'^\d+\.\s+(.+?)(?=\n\d+\.|$)'
            matches1 = re.finditer(pattern1, content, re.MULTILINE | re.DOTALL)
            
            for i, match in enumerate(matches1, 1):
                query_text = match.group(1).strip()
                # Clean up the query text
                query_text = re.sub(r'\*\*.*?\*\*', '', query_text)  # Remove markdown bold
                query_text = re.sub(r'\n+', ' ', query_text)  # Replace newlines with space
                query_text = query_text.strip()
                
                if query_text and len(query_text) > 10:  # Valid query
                    queries.append((i, query_text))
            
            # If no queries found with pattern 1, try pattern 2
            if not queries:
                # Pattern 2: "**Query N:** text"
                pattern2 = r'\*\*Query\s+(\d+):\*\*\s+(.+?)(?=\*\*Query|\Z)'
                matches2 = re.finditer(pattern2, content, re.IGNORECASE | re.DOTALL)
                
                for match in matches2:
                    query_num = int(match.group(1))
                    query_text = match.group(2).strip()
                    query_text = re.sub(r'\n+', ' ', query_text)
                    query_text = query_text.strip()
                    
                    if query_text and len(query_text) > 10:
                        queries.append((query_num, query_text))
            
            return queries
            
        except Exception as e:
            self.print_error(f"Failed to parse queries: {e}")
            return []
    
    def run_tests(self, queries: List[Tuple[int, str]]):
        """Run all tests"""
        self.print_header("AUTOMATED API TESTING - DatabaseAI")
        
        # Connect to database
        if not self.connect_database():
            self.print_error("Failed to connect to database. Exiting.")
            return
        
        time.sleep(1)  # Wait a bit after connection
        
        # Test each query
        self.print_subheader(f"Step 2: Testing {len(queries)} Queries")
        
        for query_num, query_text in queries:
            print(f"\n{Fore.CYAN}{'─' * 100}")
            print(f"{Fore.CYAN}{Style.BRIGHT}Query #{query_num}")
            print(f"{Fore.WHITE}{query_text[:120]}{'...' if len(query_text) > 120 else ''}")
            print(f"{Fore.CYAN}{'─' * 100}")
            
            result = self.test_query(query_num, query_text)
            self.results.append(result)
            
            if result["success"]:
                self.print_success(f"Query executed successfully")
                self.print_info(f"   Rows returned: {result['row_count']}")
                self.print_info(f"   Total time: {result['elapsed_time']:.2f}s")
                self.print_info(f"   Execution time: {result.get('execution_time', 0):.3f}s")
                if result['retry_count'] > 0:
                    self.print_warning(f"   Retries needed: {result['retry_count']}")
                print(f"{Fore.MAGENTA}   SQL: {result['sql_query'][:100]}{'...' if len(result['sql_query']) > 100 else ''}")
            else:
                self.print_error(f"Query failed")
                self.print_error(f"   Time: {result['elapsed_time']:.2f}s")
                if result['error']:
                    error_preview = result['error'][:200]
                    self.print_error(f"   Error: {error_preview}{'...' if len(result['error']) > 200 else ''}")
            
            # Small delay between queries
            time.sleep(0.5)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        total_time = sum(r["elapsed_time"] for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        
        total_rows = sum(r["row_count"] for r in self.results if r["success"])
        total_retries = sum(r["retry_count"] for r in self.results)
        
        # Overall stats
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Overall Statistics:")
        print(f"  Total Queries:      {total}")
        print(f"  {Fore.GREEN}Successful:         {successful} ({successful/total*100:.1f}%)")
        print(f"  {Fore.RED}Failed:             {failed} ({failed/total*100:.1f}%)")
        print(f"  {Fore.YELLOW}Total Retries:      {total_retries}")
        print(f"  {Fore.BLUE}Total Rows:         {total_rows}")
        print(f"  {Fore.BLUE}Total Time:         {total_time:.2f}s")
        print(f"  {Fore.BLUE}Average Time:       {avg_time:.2f}s")
        
        # Success rate visualization
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Success Rate:")
        success_bar = "█" * int(successful / total * 50) if total > 0 else ""
        fail_bar = "█" * int(failed / total * 50) if total > 0 else ""
        print(f"  {Fore.GREEN}{success_bar}{Fore.RED}{fail_bar} {successful}/{total}")
        
        # Failed queries detail
        if failed > 0:
            print(f"\n{Fore.RED}{Style.BRIGHT}Failed Queries:")
            for r in self.results:
                if not r["success"]:
                    print(f"  {Fore.RED}✗ Query #{r['query_num']}: {r['query_text'][:60]}...")
                    if r['error']:
                        error_line = r['error'].split('\n')[0][:80]
                        print(f"    {Fore.YELLOW}Error: {error_line}")
        
        # Queries with retries
        queries_with_retries = [r for r in self.results if r["retry_count"] > 0]
        if queries_with_retries:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Queries that needed retries:")
            for r in queries_with_retries:
                print(f"  {Fore.YELLOW}⚠ Query #{r['query_num']}: {r['query_text'][:60]}... ({r['retry_count']} retries)")
        
        # Top 5 slowest queries
        sorted_by_time = sorted(self.results, key=lambda x: x["elapsed_time"], reverse=True)[:5]
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Top 5 Slowest Queries:")
        for i, r in enumerate(sorted_by_time, 1):
            status = f"{Fore.GREEN}✓" if r["success"] else f"{Fore.RED}✗"
            print(f"  {i}. {status} Query #{r['query_num']}: {r['elapsed_time']:.2f}s - {r['query_text'][:50]}...")
        
        # Save results to JSON
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_queries": len(self.results),
                    "successful": sum(1 for r in self.results if r["success"]),
                    "failed": sum(1 for r in self.results if not r["success"]),
                    "results": self.results
                }, f, indent=2)
            
            self.print_success(f"\nResults saved to: {filename}")
        except Exception as e:
            self.print_error(f"\nFailed to save results: {e}")


def main():
    """Main function"""
    tester = APITester(API_BASE_URL)
    
    # Parse queries from TEST_QUERIES.md
    tester.print_header("Parsing Test Queries")
    queries = tester.parse_queries_from_md("TEST_QUERIES.md")
    
    if not queries:
        tester.print_error("No queries found in TEST_QUERIES.md")
        tester.print_info("Make sure TEST_QUERIES.md exists and contains numbered queries")
        return
    
    tester.print_success(f"Found {len(queries)} queries to test")
    
    # Show preview of queries
    tester.print_info("\nQuery Preview:")
    for i, (num, text) in enumerate(queries[:5], 1):
        preview = text[:80] + "..." if len(text) > 80 else text
        print(f"  {i}. {preview}")
    
    if len(queries) > 5:
        print(f"  ... and {len(queries) - 5} more queries")
    
    # Wait for user confirmation
    print(f"\n{Fore.YELLOW}Press Enter to start testing, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        return
    
    # Run tests
    tester.run_tests(queries)


if __name__ == "__main__":
    main()
