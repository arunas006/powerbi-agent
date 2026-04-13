import importlib.metadata
packages = [
"requests",
"python-dotenv",
"pydantic",
"pydantic-settings",
"openai",
"numpy",
"streamlit",
"fastapi",
"uvicorn",
"langchain",
"langchain-openai",
"langchain-community",
"langgraph",
"ipykernel",
    ]
for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} (not installed)")