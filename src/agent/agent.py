from __future__ import annotations
import os
import sys
import requests
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langchain_core.tools import tool
from src.config import get_settings
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage
from langgraph.graph import StateGraph,START,END,MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import ToolNode,tools_condition
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List,Literal,Optional,Dict,Any
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver


settings = get_settings()
fastapi_base_url = settings.BASE_URL

@tool
def check_health() -> dict:

    """
    Checks the health of the Power BI API.

    This function verifies whether the Power BI service is reachable and functioning correctly
    by attempting to retrieve an access token from the configured Power BI endpoint.
    If a valid token is successfully returned, the API is considered healthy.
    """
    try:
        response = requests.get(f"{settings.BASE_URL}/health",timeout=10)
        response.raise_for_status()
        return {"status": "healthy"}

    except requests.exceptions.RequestException as e:
        return {"status": "unhealthy", "message": str(e)}
    
@tool
def compare_workspaces() -> dict:

    """
    Compares Power BI workspaces between DEV and PROD environments.

    This function identifies dashboard reports that exist in the DEV workspace
    but are missing in the PROD workspace. It also returns the total number of
    reports present in both DEV and PROD for comparison.
    """
    settings = get_settings()

    try:
        url = f"{settings.BASE_URL}/comparison"
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        return {"status": "success", "data": response.json()}

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
@tool
def recommend_dashboards(user_query: str,top_n: int = 3) -> dict:
    
    """
    Recommend the most relevant Power BI dashboards based on a user query.

    This function analyzes a natural language query and returns the top matching
    dashboards ranked by relevance.

    Args:
        user_query (str): A natural language query describing the desired analysis
            (e.g., "looking for analysis related to supply chain pillar").
        top_n (int): The number of top dashboard recommendations to return.
    """
    settings = get_settings()

    try:
        url = f"{settings.BASE_URL}/recommend"
        params = {
            "user_query": user_query,
            "top_n": top_n
        }

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        return {"status": "success", "data": response.json()}

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
@tool
def migrate_dashboard(
    dashboard_name: str,
    from_workspace_name: str,
    to_workspace_name: str
) -> dict:
    """
    Migrate a Power BI dashboard between workspaces.

    This function transfers a specified dashboard from a source workspace
    to a target workspace, typically used for promoting content from
    development (DEV) to production (PROD).

    Args:
        dashboard_name (str): Name of the dashboard to be migrated.
        from_workspace_name (str): Source workspace name (e.g., "DEV").
        to_workspace_name (str): Target workspace name (e.g., "PROD").

    Note:
        This operation should only be executed after explicit user confirmation,
        as it may impact production environments.
    """
    settings = get_settings()

    try:
        url = f"{settings.BASE_URL}/migration"

        params = {
            "dashboard_name": dashboard_name,
            "from_workspace_name": from_workspace_name,
            "to_workspace_name": to_workspace_name
        }

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        return {
            "status": "success",
            "data": response.json()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
@tool
def delete_dashboard(
    dashboard_name: str,
    workspace_name: str
) -> dict:
    """
    Deletes a Power BI dashboard and its dataset from a workspace.

    Args:
        dashboard_name: Name of the dashboard to delete
        workspace_name: Workspace where the dashboard exists

    ⚠️ WARNING: This action is irreversible. Use only after user confirmation.
    """
    settings = get_settings()

    try:
        url = f"{settings.BASE_URL}/deletion"

        params = {
            "dashboard_name": dashboard_name,
            "workspace_name": workspace_name
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        return {
            "status": "success",
            "data": response.json()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

class AgentState(MessagesState):
    user_query: Optional[str]
    intent: Optional[str]
    clarification_count: int = 0
    is_confirmed: bool = False
    dashboard_name: Optional[str] = None
    source_workspace: Optional[str] = None
    target_workspace: Optional[str] = None

class IntentOutput(BaseModel):
    intent: Literal[
        "recommend_dashboards",
        "compare_workspaces",
        "migrate_dashboard",
        "delete_dashboard",
        "ambiguous"
    ]

system_prompt = """
        You are a helpful assistant specialized in Power BI operations.

        Your capabilities include:
        - Recommending Power BI dashboards based on user queries
        - Migrating dashboards between workspaces (Dev → Prod)
        - Deleting dashboards from Dev and Prod workspaces
        - Comparing dashboards between Dev and Prod workspaces

        Workspace Rules:
        - Valid workspace names are "Dev" and "Prod"
        - Normalize any user input (e.g., DEV, dev, PROD, prod) to "Dev" or "Prod"

        Tool Usage Guidelines:
        - Select the most appropriate tool based on the user’s intent
        - Ensure actions like migration or deletion are clearly understood before execution

        Clarification Handling:
        - If the user query is unclear, ask up to 3 relevant clarifying questions
        - If the intent is still unclear after clarification, respond with:
        "Sorry, not able to understand."

        General Behavior:
        - Be precise, structured, and action-oriented
        - Do not assume missing details—always confirm when required

        """
   


def agent_state_node(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]

    # Extract last human message safely
    user_query = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    return {
        "messages": messages,
        "user_query": user_query,
        "intent": state.get("intent"),
        "clarification_count": state.get("clarification_count", 0),
        "is_confirmed": state.get("is_confirmed", None)
    }

def clarification_node(state: AgentState):
    count = state.get("clarification_count", 0)

    # Stop after 3 attempts
    if count >= 3:
        return {
            "messages": state["messages"] + [
                AIMessage(content="Sorry, not able to understand.")
            ]
        }

    llm = ChatOpenAI(model=settings.openai_llm_model,api_key=settings.OPENAI_API_KEY.get_secret_value())

    prompt = ChatPromptTemplate.from_messages([
        ("system",system_prompt + "\n\n" + """You help clarify user intent for Power BI actions.

            Your goal is to ask ONE neutral and clear question to understand the user's intent.

            Guidelines:
            - Do NOT assume the user's intent
            - Do NOT suggest actions like migrate or delete unless explicitly mentioned
            - Offer clear choices instead of leading the user
            - Keep the question simple and specific """),
            ("human", "{question}")
            
        
    ])

    chain = prompt | llm | StrOutputParser()

    clarification_question = chain.invoke({
        "question": state["user_query"]   # 🔥 FULL CONTEXT
    })

    return {
        "messages": state["messages"] + [
            AIMessage(content=clarification_question)
        ],
        "clarification_count": count + 1
    }

def confirmation_handler(state: AgentState):
    last_msg = state["messages"][-1].content.lower()

    if last_msg in ["yes", "y"]:
        return {
            "is_confirmed": True
        }
    elif last_msg in ["no", "n"]:
        return {
            "messages": state["messages"] + [
                AIMessage(content="❌ Operation cancelled.")
            ],
            "is_confirmed": False
        }
    else:
        return {
            "messages": state["messages"] + [
                AIMessage(content="Please reply with 'yes' or 'no'.")
            ]
        }
    
router_prompt = """
You are an expert AI agent that classifies user intent for Power BI operations.

Your task is to understand the user's goal and classify it into ONE of the following intents:

1. recommend_dashboards  
   → User is looking for suggestions, insights, or relevant dashboards based on a topic

2. compare_workspaces  
   → User wants to understand differences, gaps, discrepancies, or missing dashboards 
     between Dev and Prod workspaces

3. migrate_dashboard  
   → User wants to move, promote, or deploy a dashboard from one workspace (Dev) to another (Prod)

4. delete_dashboard  
   → User wants to remove or delete a dashboard from a workspace

5. ambiguous  
   → The user intent is unclear, incomplete, or cannot be confidently mapped

---

Guidelines:
- Focus on the USER'S GOAL, not keywords
- Use the full conversation context
- If the user replies with short answers like "yes", "ok", infer intent from previous messages
- Prefer compare_workspaces when the user is asking about differences, gaps, or missing items
- Only select migrate_dashboard or delete_dashboard if the user clearly intends an ACTION
- If unsure → return "ambiguous"
- Do NOT ask questions
- Do NOT explain

Return only the intent.
"""

def router_decision(state: AgentState):
    llm = ChatOpenAI(model=settings.openai_llm_model,api_key=settings.OPENAI_API_KEY.get_secret_value())

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\n" + router_prompt),
        ("placeholder", "{messages}")   # 🔥 CRITICAL
    ])


    chain = prompt | llm.with_structured_output(IntentOutput)

    response = chain.invoke({"messages": state["messages"]})

    return {
        "intent": response.intent
    }

def route_selector(state: AgentState):
    return state["intent"]

def confirmation_node(state: AgentState):
    dashboard = state.get("dashboard_name")
    source = state.get("source_workspace")
    target = state.get("target_workspace")
    intent = state.get("intent")


    if intent=="migrate_dashboard":

        # If still missing → ask again
        if not all([dashboard, source, target]):
            return {
                "messages": state["messages"] + [
                    AIMessage(content="""
                ⚠️ Missing required details for migration.

                Please provide:
                dashboard_name, source_workspace, target_workspace

                Example:
                invoice-dashboard, dev, prod
                """)
                            ]
                        }

        return {
            "messages": state["messages"] + [
                AIMessage(content=f"""
            ⚠️ You are about to MIGRATE a dashboard.

            Details:
            - Dashboard: {dashboard}
            - From: {source}
            - To: {target}

            👉 Please confirm to proceed (yes/no)
            """.strip())
                    ]
                }
    else:
        if not all([dashboard, target]):
            return {
                "messages": state["messages"] + [
                    AIMessage(content="""
                ⚠️ Missing required details for deletion.

                Please provide:
                dashboard_name, target_workspace

                Example:
                invoice-dashboard, Prod
                """)
                            ]
                        }
        return {
            "messages": state["messages"] + [
                AIMessage(content=f"""
            ⚠️ You are about to Delete a dashboard.

            Details:
            - Dashboard: {dashboard}
            - From: {target}

            👉 Please confirm to proceed (yes/no)
            """.strip())
                    ]
                }
    
def parse_migration_input(state: AgentState):
    last_msg = state["messages"][-1].content.strip()

    intent = state["intent"]

    # Try parsing input
    parts = [p.strip() for p in last_msg.split(",")]

    if intent=="migrate_dashboard":


        if len(parts) == 3:
            return {
                "dashboard_name": parts[0],
                "source_workspace": parts[1],
                "target_workspace": parts[2]
            }

        # ❌ If not proper input → ASK USER
        return {
            "messages": state["messages"] + [
                AIMessage(content="""
                    Please provide the required details in this format:

                    dashboard_name, source_workspace, target_workspace

                    Example:
                    invoice-dashboard, dev, prod
                    """)
                            ]
                        }
    else:
        if len(parts)==2:
            return {
                "dashboard_name": parts[0],
                "target_workspace": parts[1]
            }
        return {"messages": state["messages"] + [
                AIMessage(content="""
                    Please provide the required details in this format:

                    dashboard_name, target_workspace

                    Example:
                    invoice-dashboard,prod
                    """)
                            ]
                        }

def entry_router(state: AgentState):
    last_msg = state["messages"][-1].content.lower().strip()

    # ✅ confirmation response
    if last_msg in ["yes", "no", "y", "n"]:
        return "confirmation"

    # ✅ input details (simple heuristic)
    if state.get("intent") in ["migrate_dashboard", "delete_dashboard"] and "," in last_msg:
        return "input"
        

    return "router"

def health_check_node(state: AgentState):
    result = check_health.invoke({}) 

    if result.get("status") != "healthy":
        return {
            "messages": state["messages"] + [
                AIMessage(content="❌ Power BI API is down. Aborting request.")
            ]
        }

    return state

def tool_executor(state: AgentState):
    """
    Based on the User Intent, execute the appropriate tool
    """
    intent = state["intent"]
    query = state["user_query"]

    if intent == "recommend_dashboards":
        result = recommend_dashboards.invoke({
            "user_query": query,
            "top_n": 3
        })

    elif intent == "compare_workspaces":
        result = compare_workspaces.invoke({})

    elif intent == "migrate_dashboard":
        dashboard = state.get("dashboard_name")
        source = state.get("source_workspace")
        target = state.get("target_workspace")
        if not all([dashboard, source, target]):
            return {
                "messages": state["messages"] + [
                    AIMessage(content="⚠️ Missing details. Please specify dashboard, source, and target.")
                ]
            }

        result = migrate_dashboard.invoke({
            "dashboard_name": dashboard,
            "from_workspace_name": source,
            "to_workspace_name": target
        })

    elif intent == "delete_dashboard":
        dashboard = state.get("dashboard_name")
        target = state.get("target_workspace")
        if not all([dashboard,target]):
            return {
                "messages": state["messages"] + [
                    AIMessage(content="⚠️ Missing details. Please specify dashboard and target workspace.")
                ]
            }

        result = delete_dashboard.invoke({
            "dashboard_name": dashboard,
            "workspace_name": target
        })

    else:
        return {
            "messages": state["messages"] + [
                AIMessage(content="Sorry, not able to understand.")
            ]
        }

    return {
        "messages": state["messages"] + [
            AIMessage(content=str(result))
        ]
    }


memory = MemorySaver()

graph = StateGraph(AgentState)

graph.add_node("Question_Receiver", agent_state_node)
graph.add_node("Router", router_decision)
graph.add_node("Clarification", clarification_node)
graph.add_node("InputParser", parse_migration_input)
graph.add_node("Confirmation", confirmation_node)
graph.add_node("ConfirmationHandler", confirmation_handler)
graph.add_node("HealthCheck", health_check_node)
graph.add_node("ToolExecutor", tool_executor)

# ENTRY
graph.add_edge(START, "Question_Receiver")

graph.add_conditional_edges(
    "Question_Receiver",
    entry_router,
    {
        "router": "Router",
        "confirmation": "ConfirmationHandler",
        "input": "InputParser"
    }
)


# ROUTER
graph.add_conditional_edges(
    "Router",
    route_selector,
    {
        "recommend_dashboards": "HealthCheck",
        "compare_workspaces": "HealthCheck",
        "migrate_dashboard": "InputParser",  
        "delete_dashboard": "InputParser",
        "ambiguous": "Clarification"
    }
)

# CLARIFICATION
graph.add_conditional_edges(
    "Clarification",
    lambda state: "end" if state.get("clarification_count", 0) >= 3 else "continue",
    {
        "continue": "Router",
        "end": END
    }
)

# INPUT → CONFIRM
graph.add_edge("InputParser", "Confirmation")

# CONFIRM → HANDLE
graph.add_edge("Confirmation", "ConfirmationHandler")

graph.add_conditional_edges(
    "ConfirmationHandler",
    lambda state: "proceed" if state.get("is_confirmed") else "end",
    {
        "proceed": "HealthCheck",
        "end": END
    }
)

# EXECUTION
graph.add_edge("HealthCheck", "ToolExecutor")
graph.add_edge("ToolExecutor", END)

# COMPILE
agent = graph.compile(
    checkpointer=memory,
    interrupt_after=["Confirmation"]  # ✅ now valid
)

if __name__ == "__main__":
    
    

    # thread = {"configurable": {"thread_id": "2"}}
    # response = agent.invoke(
    # {
    #     "messages": [
    #         SystemMessage(content=system_prompt),
    #         HumanMessage(
    #             content="I want to migrate the Sales-Dashboard from dev to prod")
    #     ]
    # },
    # config=thread
    # )

    # print(response["messages"][-1].content)

    # thread = {"configurable": {"thread_id": "2"}}
    # response = agent.invoke(
    # {
    #     "messages": [
    #         SystemMessage(content=system_prompt),
    #         HumanMessage(
    #             content="Sales-Dashboard, Dev, Prod")
    #     ]
    # },
    # config=thread
    # )

    # print(response["messages"][-1].content)

    # thread = {"configurable": {"thread_id": "2"}}
    # response = agent.invoke(
    # {
    #     "messages": [
    #         SystemMessage(content=system_prompt),
    #         HumanMessage(
    #             content="yes")
    #     ]
    # },
    # config=thread
    # )

    # print(response["messages"][-1].content)

    thread = {"configurable": {"thread_id": "3"}}
    response = agent.invoke(
    {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="I need to delete Sales-Dashboard from prod")
        ]
    },
    config=thread
    )

    print(response["messages"][-1].content)

    thread = {"configurable": {"thread_id": "3"}}
    response = agent.invoke(
    {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Sales-Dashboard, Prod")
        ]
    },
    config=thread
    )

    print(response["messages"][-1].content)

    thread = {"configurable": {"thread_id": "3"}}
    response = agent.invoke(
    {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="yes")
        ]
    },
    config=thread
    )

    print(response["messages"][-1].content)


