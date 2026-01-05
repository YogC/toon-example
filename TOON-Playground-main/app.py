"""
TOON Playground - FastAPI Backend
Interactive playground for comparing JSON, YAML, and TOON formats
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
from dotenv import load_dotenv

from toon_encoder import json_to_toon, json_to_yaml, count_tokens

# Load environment variables
load_dotenv()

app = FastAPI(title="TOON Playground", version="1.0.0")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class ConvertRequest(BaseModel):
    json_data: str


class LLMRequest(BaseModel):
    format: str  # 'json', 'yaml', or 'toon'
    data: str
    prompt: str


class TokenComparisonResponse(BaseModel):
    json_format: dict
    yaml_format: dict
    toon_format: dict


@app.get("/")
async def root():
    """Serve the main playground page"""
    return FileResponse("static/index.html")


@app.post("/api/convert")
async def convert_formats(request: ConvertRequest):
    """Convert JSON to all formats and return with token counts"""
    try:
        # Validate JSON
        json_data = json.loads(request.json_data)
        
        # Format JSON nicely
        json_formatted = json.dumps(json_data, indent=2)
        json_compact = json.dumps(json_data, separators=(',', ':'))
        
        # Convert to YAML
        yaml_formatted = json_to_yaml(request.json_data)
        
        # Convert to TOON
        toon_formatted = json_to_toon(request.json_data)
        
        # Count tokens for each
        json_tokens = count_tokens(json_formatted)
        json_compact_tokens = count_tokens(json_compact)
        yaml_tokens = count_tokens(yaml_formatted)
        toon_tokens = count_tokens(toon_formatted)
        
        # Calculate savings
        json_savings = ((json_tokens - toon_tokens) / json_tokens * 100) if json_tokens > 0 else 0
        yaml_savings = ((yaml_tokens - toon_tokens) / yaml_tokens * 100) if yaml_tokens > 0 else 0
        
        return {
            "success": True,
            "formats": {
                "json": {
                    "formatted": json_formatted,
                    "compact": json_compact,
                    "tokens": json_tokens,
                    "tokens_compact": json_compact_tokens
                },
                "yaml": {
                    "formatted": yaml_formatted,
                    "tokens": yaml_tokens
                },
                "toon": {
                    "formatted": toon_formatted,
                    "tokens": toon_tokens
                }
            },
            "comparison": {
                "toon_vs_json": {
                    "savings_percent": round(json_savings, 1),
                    "tokens_saved": json_tokens - toon_tokens
                },
                "toon_vs_yaml": {
                    "savings_percent": round(yaml_savings, 1),
                    "tokens_saved": yaml_tokens - toon_tokens
                }
            }
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


@app.post("/api/llm-test")
async def test_with_llm(request: LLMRequest):
    """Send data to OpenAI and get response"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key not found. Please add OPENAI_API_KEY to .env file"
            )
        
        client = OpenAI(api_key=api_key)
        
        # Construct the full prompt
        full_prompt = f"{request.prompt}\n\nData:\n{request.data}"
        
        # Count input tokens
        input_tokens = count_tokens(full_prompt)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        output_text = response.choices[0].message.content
        output_tokens = count_tokens(output_text)
        
        return {
            "success": True,
            "format_used": request.format,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "response": output_text,
            "model": "gpt-4o-mini"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")


@app.get("/api/examples")
async def get_examples():
    """Return example data for the playground"""
    examples = {
        "simple_users": {
            "name": "Simple Users",
            "description": "Basic user list - perfect for TOON's tabular format",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice", "role": "admin", "active": True},
                    {"id": 2, "name": "Bob", "role": "user", "active": True},
                    {"id": 3, "name": "Charlie", "role": "user", "active": False}
                ]
            }
        },
        "products": {
            "name": "Product Catalog",
            "description": "E-commerce products with uniform structure",
            "data": {
                "products": [
                    {"id": 301, "name": "Wireless Mouse", "price": 29.99, "stock": 150},
                    {"id": 302, "name": "Mechanical Keyboard", "price": 89.00, "stock": 45},
                    {"id": 303, "name": "USB-C Hub", "price": 45.50, "stock": 200}
                ]
            }
        },
        "analytics": {
            "name": "Analytics Data",
            "description": "Time-series metrics - shows TOON's efficiency",
            "data": {
                "metrics": [
                    {"date": "2025-01-01", "views": 5715, "clicks": 211, "conversions": 28, "revenue": 7976.46},
                    {"date": "2025-01-02", "views": 7103, "clicks": 393, "conversions": 28, "revenue": 8360.53},
                    {"date": "2025-01-03", "views": 7248, "clicks": 378, "conversions": 24, "revenue": 3212.57},
                    {"date": "2025-01-04", "views": 2927, "clicks": 77, "conversions": 11, "revenue": 1211.69}
                ]
            }
        },
        "nested": {
            "name": "Nested Structure",
            "description": "Mixed structure with nested objects and arrays",
            "data": {
                "context": {
                    "task": "Our favorite hikes together",
                    "location": "Boulder",
                    "season": "spring_2025"
                },
                "friends": ["ana", "luis", "sam"],
                "hikes": [
                    {
                        "id": 1,
                        "name": "Blue Lake Trail",
                        "distanceKm": 7.5,
                        "elevationGain": 320,
                        "companion": "ana",
                        "wasSunny": True
                    },
                    {
                        "id": 2,
                        "name": "Ridge Overlook",
                        "distanceKm": 9.2,
                        "elevationGain": 540,
                        "companion": "luis",
                        "wasSunny": False
                    }
                ]
            }
        }
    }
    
    return {"examples": examples}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
