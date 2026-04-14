import streamlit as st
import requests
from src.config import Settings

# ---------------- CONFIG ----------------
settings = Settings()
API_URL = f"{settings.AGENT_URL}/chat"

st.set_page_config(
    page_title="Power BI Agent",
    page_icon="🤖",
    layout="wide"
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
.block-container { padding-top: 1rem; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #003366 0%, #002244 100%);
}

/* Chat card */
.chat-card {
    background: #111827;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #374151;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🤖 Power BI Agent</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🤖 AI Agent")

    if st.button("➕ New Chat"):
        st.session_state.messages = []

    thread_id = st.text_input("Thread ID", value="user_1")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- CHAT DISPLAY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- INPUT ----------------
prompt = st.chat_input("Ask something...")

if prompt:
    # USER MESSAGE
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # API CALL
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            try:
                payload = {
                    "message": prompt,
                    "thread_id": thread_id
                }

                response = requests.post(API_URL, json=payload, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    payload = data.get("data", {})

                    # ---------------- DASHBOARD RECOMMENDATION ----------------
                    if "dashboards" in payload:
                        dashboards = payload["dashboards"]

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": dashboards
                        })

                        for dash in dashboards:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(145deg, #0f172a, #1e293b);
                                padding: 18px;
                                border-radius: 14px;
                                margin-bottom: 12px;
                                border: 1px solid #334155;
                            ">
                                <h3 style="color:#38bdf8;">📊 {dash['Selected_Dashboard']}</h3>
                                <p style="color:#cbd5f5;">💡 {dash['Reason']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    # ---------------- MIGRATION ----------------
                    elif "dataset_id" in payload:
                        st.success("🚀 Migration Completed Successfully")

                        st.markdown(f"""
                        <div style="
                            background:#022c22;
                            padding:15px;
                            border-radius:10px;
                            border:1px solid #065f46;
                        ">
                            <p>📦 <b>Dataset ID:</b> {payload['dataset_id']}</p>
                            <p>📊 <b>Report ID:</b> {payload['report_id']}</p>
                            <p>✅ <b>Status:</b> {payload['status']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Migration Success\nDataset: {payload['dataset_id']}"
                        })

                    # ---------------- COMPARISON ----------------
                    elif "status" in payload and "counts" in payload["status"]:
                        stats = payload["status"]

                        st.info("⚖️ Dashboard Comparison Result")

                        st.markdown(f"""
                        <div style="
                            background:#1e293b;
                            padding:15px;
                            border-radius:10px;
                            border:1px solid #334155;
                        ">
                            <p>📊 Dev Total: {stats['counts']['dev_total']}</p>
                            <p>📊 Prod Total: {stats['counts']['prod_total']}</p>
                            <p>❌ Missing in Prod: {stats['counts']['missing_in_prod']}</p>
                            <p>❌ Missing in Dev: {stats['counts']['missing_in_dev']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "Comparison completed"
                        })

                    # ---------------- DELETION ----------------
                    elif "Dashboard_name" in payload:
                        st.warning("🗑️ Dashboard Deleted")

                        st.markdown(f"""
                        <div style="
                            background:#3f1d1d;
                            padding:15px;
                            border-radius:10px;
                            border:1px solid #7f1d1d;
                        ">
                            <p>📊 <b>Dashboard:</b> {payload['Dashboard_name']}</p>
                            <p>🆔 <b>Resource ID:</b> {payload['resource_id']}</p>
                            <p>✅ {payload['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Deleted {payload['Dashboard_name']}"
                        })

                    # ---------------- FALLBACK ----------------
                    else:
                        st.error("Unknown response format")
                        st.write(data)

            except requests.exceptions.Timeout:
                st.error("⏰ The request timed out. Please try again.")