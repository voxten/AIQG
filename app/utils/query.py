import ollama
import pandas as pd
from typing import List, Tuple, Any


def generate_sql(user_query: str, schema: str) -> str:
    """Generate SQL from natural language"""
    prompt = f"""
    You are an expert SQL query generator for MySQL databases.

    ### Instructions:
    - Generate ONLY the SQL query that answers the user's question
    - DO NOT include any explanations, comments, or additional text
    - DO NOT wrap the SQL in markdown or code blocks
    - DO NOT include any Python code or pseudocode
    - The output must be a SINGLE, VALID MySQL query ending with semicolon

    ### Database Schema:
    {schema}

    ### User Question:
    {user_query}

    ### SQL Query:
    """

    response = ollama.generate(model="sqlcoder:15b", prompt=prompt)
    raw_sql = response["response"].strip()
    print("DEBUG RAW SQL FROM MODEL:")
    print(raw_sql)  # To help debug what the model returns

    # Extract SQL from the response
    sql = extract_sql_from_response(raw_sql)
    return sql


def extract_sql_from_response(response: str) -> str:
    """Extract clean SQL from model response"""
    # Remove everything after the semicolon if there are additional explanations
    if ';' in response:
        response = response.split(';')[0] + ';'

    # Remove common wrappers
    response = response.strip()
    if response.startswith("```sql"):
        response = response[6:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]

    # Split lines and remove empty lines and comments
    lines = []
    for line in response.split('\n'):
        line = line.strip()
        if not line or line.startswith('--') or line.startswith('#'):
            continue
        # Remove any trailing explanations
        if ';' in line:
            line = line.split(';')[0] + ';'
        lines.append(line)

    sql = ' '.join(lines).strip()

    # Ensure it ends with semicolon
    if not sql.endswith(';'):
        sql += ';'

    # Final validation
    if not sql.lower().startswith(('select ', 'insert ', 'update ', 'delete ', 'with ')):
        raise ValueError("The response doesn't contain a valid SQL query")

    return sql
def explain_query(sql: str, schema: str) -> str:
    """Explain SQL query"""
    explain_prompt = f"""
    Explain this SQL query in simple terms:
    {sql}

    Database Schema:
    {schema}

    Provide:
    1. What the query does
    2. Potential performance considerations
    3. Any suggestions for improvement
    """
    explanation = ollama.generate(model="sqlcoder", prompt=explain_prompt)
    return explanation["response"]


def prepare_results(columns: List[str], results: Any) -> Tuple[pd.DataFrame, str]:
    """Prepare query results for display"""
    df = pd.DataFrame(results, columns=columns)
    csv = df.to_csv(index=False).encode('utf-8')
    return df, csv


def clean_generated_sql(raw_sql: str) -> str:
    cleaned = raw_sql.strip().strip('`').strip('"').strip("'")

    # Simple safety check: look for known non-SQL patterns
    forbidden_patterns = ["import ", "def ", "create_engine", "sqlalchemy", "print(", "input(", "while ", "try:"]
    if any(pat in cleaned.lower() for pat in forbidden_patterns):
        print("DEBUG: Model output was:", cleaned)  # log
        raise ValueError("The model returned non-SQL code. Please try again.")

    if not cleaned.endswith(";"):
        cleaned += ";"

    return cleaned

