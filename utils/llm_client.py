"""
LLM client module for AI Insights page.
Handles OpenAI API integration with secure API key management.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class AIInsightResponse:
    """Structured response from the AI model."""
    summary_text: str
    filters: Dict[str, Any]
    chart: Dict[str, Any]
    error: Optional[str] = None


def is_api_key_configured() -> bool:
    """Check if OpenAI API key is configured in environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key is not None and len(api_key) > 0


def get_data_schema_description(
    columns: List[str],
    years: List[int],
    regions: List[str],
    sizes: List[str],
    sample_institutions: List[str],
    stats: Dict[str, Dict[str, float]]
) -> str:
    """
    Generate a description of the available data schema for the LLM prompt.
    
    Args:
        columns: List of column names in the dataset
        years: List of available years
        regions: List of available regions
        sizes: List of institution size categories
        sample_institutions: Sample of institution names
        stats: Dictionary with aggregate statistics for key metrics
    """
    schema_description = f"""
## Available Data Schema

You have access to higher education enrollment data from IPEDS (Integrated Postsecondary Education Data System).

### Columns Available:
- **institution_name**: Name of the higher education institution (string)
- **year**: Academic year (integer) - Available years: {sorted(years)}
- **state**: US state abbreviation (string, e.g., "CA", "NY", "TX")
- **region**: US Census region (string) - Values: {regions}
- **institution_size**: Size category (string) - Values: {sizes}
- **applicants**: Number of first-time undergraduate applicants (integer)
- **admissions**: Number of students admitted (integer)
- **enrolled_total**: Number of students who enrolled (integer)
- **admit_rate**: Admission rate (admissions/applicants * 100) - percentage
- **yield_rate**: Yield rate (enrolled/admissions * 100) - percentage
- **pct_hispanic**: Percentage of Hispanic/Latino students
- **pct_white**: Percentage of White students
- **pct_black**: Percentage of Black students
- **pct_asian**: Percentage of Asian students
- **pct_other**: Percentage of students from other racial/ethnic groups
- **diversity_index**: A calculated diversity index (0-100 scale)

### Aggregate Statistics (across all data):
"""
    for metric, metric_stats in stats.items():
        schema_description += f"- **{metric}**: min={metric_stats.get('min', 'N/A'):.1f}, max={metric_stats.get('max', 'N/A'):.1f}, avg={metric_stats.get('avg', 'N/A'):.1f}\n"
    
    schema_description += f"""
### Sample Institution Names:
{', '.join(sample_institutions[:10])}

### Filter Keys (use in the "filters" object):
- **year**: Single integer year (e.g., 2024)
- **regions**: List of region strings (e.g., ["Northeast", "Midwest"])
- **sizes**: List of size category strings (e.g., ["Large", "Medium"])
- **institutions**: List of institution name strings (exact match required)

### Chart Types Supported:
- **bar**: Horizontal bar chart (good for ranking/comparing institutions)
- **scatter**: Scatter plot (good for showing relationships between two metrics)
- **line**: Line chart (good for trends over time)
"""
    return schema_description


def build_system_prompt(data_schema: str) -> str:
    """Build the system prompt for the LLM."""
    return f"""You are an AI analytics assistant for a higher education enrollment dashboard.
Your task is to analyze user questions about enrollment data and return a structured JSON response.

{data_schema}

## Response Format

You MUST respond with ONLY a valid JSON object (no markdown, no explanation outside JSON).
The JSON must have exactly this structure:

{{
  "summary_text": "A concise but insightful 2-4 sentence explanation answering the user's question in the context of enrollment analytics. Use specific numbers when possible.",
  "filters": {{
    "year": 2024,
    "regions": ["Northeast", "Midwest"],
    "sizes": ["Large"],
    "institutions": []
  }},
  "chart": {{
    "type": "bar",
    "x": "institution_name",
    "y": "yield_rate",
    "sort": "desc",
    "top_n": 10
  }}
}}

## Field Requirements:

### summary_text (required):
- Provide an executive-style insight answering the user's question
- Be specific and data-driven
- Keep it to 2-4 sentences

### filters (optional):
- Only include keys that should filter the data
- Use only these keys: year, regions, sizes, institutions
- year: single integer
- regions: list of strings from available regions
- sizes: list of strings from available sizes
- institutions: list of exact institution name strings
- Omit a key entirely if no filter is needed for it

### chart (required):
- type: "bar", "scatter", or "line"
- x: column name for x-axis
- y: column name for y-axis
- For bar charts: use "institution_name" for x when comparing institutions
- sort: "desc" or "asc" (optional, for bar charts)
- top_n: integer limit (optional, for bar charts, default 10)
- color: column name for color grouping (optional)

## Important Rules:
1. Output ONLY valid JSON - no markdown code blocks, no text before or after
2. Use exact column names as provided in the schema
3. For institution comparisons, always use bar chart with institution_name on x-axis
4. For time trends, use line chart with year on x-axis
5. For metric relationships, use scatter chart
6. Always provide meaningful filters that make sense for the question
"""


def _extract_response_text(response: Any) -> str:
    """Extract text content from an OpenAI Responses API object."""
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""

    chunks: List[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if content is None and isinstance(item, dict):
            content = item.get("content")

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") in {"output_text", "text"}:
                        text = block.get("text")
                        if text:
                            chunks.append(text)
                else:
                    text = getattr(block, "text", None)
                    if text:
                        chunks.append(text)
        elif isinstance(content, str):
            chunks.append(content)

    return "\n".join(chunks).strip()


def parse_ai_response(response_text: str) -> AIInsightResponse:
    """
    Parse the AI response text into a structured AIInsightResponse.
    
    Handles JSON extraction and validation with fallback for errors.
    """
    try:
        # Try to extract JSON from the response
        # Sometimes LLMs wrap JSON in markdown code blocks
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        data = json.loads(text)
        
        # Validate required fields
        summary_text = data.get("summary_text", "")
        if not summary_text:
            summary_text = "The AI generated a response but did not provide a summary."
        
        filters = data.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}
        
        chart = data.get("chart", {})
        if not isinstance(chart, dict):
            chart = {"type": "bar", "x": "institution_name", "y": "yield_rate", "top_n": 10}
        
        # Ensure chart has required fields
        if "type" not in chart:
            chart["type"] = "bar"
        if "x" not in chart:
            chart["x"] = "institution_name"
        if "y" not in chart:
            chart["y"] = "yield_rate"
        
        return AIInsightResponse(
            summary_text=summary_text,
            filters=filters,
            chart=chart
        )
        
    except json.JSONDecodeError as e:
        return AIInsightResponse(
            summary_text="",
            filters={},
            chart={},
            error=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        return AIInsightResponse(
            summary_text="",
            filters={},
            chart={},
            error=f"Unexpected error parsing AI response: {str(e)}"
        )


def generate_ai_insight(
    user_query: str,
    data_schema: str,
) -> AIInsightResponse:
    """
    Generate AI insight using OpenAI API.
    
    Args:
        user_query: The user's natural language question
        data_schema: Description of available data schema
        
    Returns:
        AIInsightResponse with summary, filters, and chart specification
    """
    # Check API key
    if not is_api_key_configured():
        return AIInsightResponse(
            summary_text="",
            filters={},
            chart={},
            error="AI features are not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = build_system_prompt(data_schema)
        
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {"type": "input_text", "text": system_prompt}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_query}
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            }
        )
        
        response_text = _extract_response_text(response)
        if not response_text:
            return AIInsightResponse(
                summary_text="",
                filters={},
                chart={},
                error="AI service error: empty response received."
            )
        return parse_ai_response(response_text)
        
    except ImportError:
        return AIInsightResponse(
            summary_text="",
            filters={},
            chart={},
            error="OpenAI package is not installed. Please run: pip install openai"
        )
    except Exception as e:
        error_msg = str(e)
        # Don't expose full error details that might contain sensitive info
        if "api_key" in error_msg.lower():
            error_msg = "Invalid or expired API key. Please check your OPENAI_API_KEY."
        elif "rate" in error_msg.lower():
            error_msg = "API rate limit exceeded. Please try again later."
        elif "connection" in error_msg.lower():
            error_msg = "Failed to connect to OpenAI API. Please check your internet connection."
        else:
            error_msg = f"AI service error: {error_msg[:100]}"
        
        return AIInsightResponse(
            summary_text="",
            filters={},
            chart={},
            error=error_msg
        )
