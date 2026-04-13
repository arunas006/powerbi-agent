from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from src.agent.agent import agent


# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str


# ---------- App ----------
app = FastAPI(
    title="Power BI Agent API",
    description="AI-powered agent for managing Power BI dashboards",
    version="1.0.0"
)


# ---------- CORS Middleware ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Thread Pool for Timeout ----------
executor = ThreadPoolExecutor(max_workers=5)


# ---------- API ----------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    system_prompt = """
    You are a helpful assistant specialized in Power BI operations.
    """

    thread = {"configurable": {"thread_id": req.thread_id}}

    def run_agent():
        return agent.invoke(
            {
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=req.message)
                ]
            },
            config=thread
        )

    try:
        # ⏱️ Timeout set to 20 seconds (adjust as needed)
        future = executor.submit(run_agent)
        result = future.result(timeout=20)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "response": result["messages"][-1].content
    }
