import ollama
import pandas as pd
from typing import List, Tuple, Any


def generate_sql(user_query: str, schema: str) -> str:
    """Generate SQL from natural language"""
    prompt = f"""
    You are a SQL expert. Convert this natural language to valid MySQL syntax query: 
    Database Schema:
    {schema}
    Query: "{user_query}"
    Rules:
    - Use ONLY the tables/columns above.
    - Return ONLY SQL, no explanations.
    - Avoid `+` for concatenation (use `CONCAT()`).
    - Don't use */ or ---------- on start of your answer
    - Use `IFNULL()` instead of `COALESCE()` if needed.
    - For dates, use `YYYY-MM-DD` format.
    """
    response = ollama.generate(model="sqlcoder", prompt=prompt)
    return response["response"].strip()


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