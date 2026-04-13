import numpy as np
from openai import OpenAI
from src.config import get_settings
from pathlib import Path
import json
import re
from typing import List

from pydantic import BaseModel

class DashboardItem(BaseModel):
    Selected_Dashboard: str
    Reason: str

class DashboardResponse(BaseModel):
    dashboards: List[DashboardItem]

settings = get_settings()
API_KEY = settings.OPENAI_API_KEY.get_secret_value()
model = settings.openai_llm_model
embed_model = settings.EMBEDDING_MODEL

client = OpenAI(api_key=API_KEY)

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_PATH = BASE_DIR /"report_metadata.json"

with open(METADATA_PATH, "r") as f:
    metadata = json.load(f)

# print(metadata)

EMBED_CACHE: dict[str, list[float]] = {}

def embedding(text: str) -> list[float]:
    if text in EMBED_CACHE:
        return EMBED_CACHE[text]
    query = text
    response = client.embeddings.create(input=query, model=embed_model)
    embedding = response.data[0].embedding
    EMBED_CACHE[text] = embedding

    return embedding

def cosine_similarity(a, b) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def build_report_text(report_name: str) -> str:
    meta = metadata.get(report_name, {})

    return f"""
    dashboard name: {report_name}
    objective: {meta.get('objective', '')}
    domain: {meta.get('domain', '')}
    tags: {' '.join(meta.get('tags', [])).lower()}
    """

def return_top_reports(query: str,top_n: int) -> list[str]:

    query_embedding = embedding(query) 
    report_scores = {}
    for report in metadata:
        report_text = build_report_text(report)
        report_embedding = embedding(report_text)

        score = cosine_similarity(query_embedding, report_embedding)
        report_scores[report] = score 
 
    results = sorted(report_scores.items(), key=lambda x: x[1], reverse=True)
    return [report for report, _ in results[:top_n]]

def build_prompt(user_query: str, top_reports: list[str]) -> str:

    report_details = {
        report : metadata[report] for report in top_reports
    }

    return f"""
    You are a Power BI Dashboard Assistant.

    User Requirement:
    {user_query}

    Candidate Dashboards:
    {json.dumps(report_details, indent=2)}

    Instructions:
    - Understand the requirement carefully
    - Compare dashboards using objective, domain, and tags
    - Select the BEST matching dashboard
    - If multiple match, choose the most relevant
    - If unclear → ask a follow-up question
    - If no match → return "None"

    Return strictly JSON:
    {{
    "Selected_Dashboard": "<dashboard_name>",
    "Reason": "<short explanation>"
    }}

    """

def llm_select_dashboard(user_query: str, candidates: list[str]) -> DashboardResponse:

    candidate_details = {
        report: metadata.get(report, {})
        for report in candidates
    }

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert BI assistant."},
            {
                "role": "user",
                "content": f"""
    User Requirement:
    {user_query}

    Candidate Dashboards:
    {json.dumps(candidate_details, indent=2)}

     Instructions:
    - Understand the requirement carefully
    - Compare dashboards using objective, domain, and tags
    - Select the BEST matching dashboard
    - If multiple match, choose the most relevant
    - If unclear → ask a follow-up question
    - If no match → return "None"

    Select the BEST 2 dashboards based on relevance.
    """
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "dashboard_selection",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dashboards": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "Selected_Dashboard": {"type": "string"},
                                        "Reason": {"type": "string"}
                                    },
                                    "required": ["Selected_Dashboard", "Reason"]
                                },
                                "minItems": 1,
                                "maxItems": 2
                            }
                        },
                        "required": ["dashboards"]
                    }
                }
            },
            temperature=0.2
        )

    output = response.choices[0].message.content


    try:
        return DashboardResponse.model_validate_json(output)
    except:
        # fallback cleanup
        cleaned = re.sub(r"```json\s*|```", "", output).strip()
        return DashboardResponse.model_validate_json(cleaned)


def recommend_dashboard(user_query: str,top_n: int=3) -> dict:
    top_reports = return_top_reports(user_query, top_n)
    return llm_select_dashboard(user_query, top_reports)

if __name__ == "__main__":
    print(recommend_dashboard("looking for analysis related to supply chain pillar", 3))
    





