import streamlit as st
import requests
import copy

from src.config import Settings

# ---------------- CONFIG ----------------
settings = Settings()
API_URL = f"{settings.AGENT_URL}/chat"

st.set_page_config(
    page_title="Power BI Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Power BI Agent")

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# ---------------- DISPLAY CHAT HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):

        if isinstance(msg["content"], list):
            # Dashboard cards
            for dash in msg["content"]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, #0f172a, #1e293b);
                    padding: 15px;
                    border-radius: 12px;
                    margin-bottom: 10px;
                    border: 1px solid #334155;
                ">
                    <b style="color:#38bdf8;">📊 {dash.get('Selected_Dashboard')}</b><br>
                    <span style="color:#cbd5f5;">💡 {dash.get('Reason')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Ask something about Power BI...")

if user_input and not st.session_state.processing:

    st.session_state.processing = True

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"message": user_input, "thread_id": "25"},
                    timeout=60
                )

                if response.status_code != 200:
                    st.error(f"API Error: {response.status_code}")
                    st.session_state.processing = False
                    st.stop()

                data = response.json()

                # 🔍 DEBUG (optional)
                # st.write("RAW RESPONSE:", data)

                # ======================================================
                # ✅ CASE 1: STRUCTURED RESPONSE
                # ======================================================
                if isinstance(data, dict) and "status" in data:

                    payload = data.get("data", {})

                    if data.get("status") == "success":

                        # -------- DASHBOARDS --------
                        if "dashboards" in payload:
                            dashboards = payload["dashboards"]

                            for dash in dashboards:
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(145deg, #0f172a, #1e293b);
                                    padding: 15px;
                                    border-radius: 12px;
                                    margin-bottom: 10px;
                                    border: 1px solid #334155;
                                ">
                                    <b style="color:#38bdf8;">📊 {dash.get('Selected_Dashboard')}</b><br>
                                    <span style="color:#cbd5f5;">💡 {dash.get('Reason')}</span>
                                </div>
                                """, unsafe_allow_html=True)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": copy.deepcopy(dashboards)
                            })

                        # -------- MIGRATION --------
                        elif any(k in payload for k in ["dataset_id", "report_id", "datasetId"]):

                            st.success("🚀 Migration Completed Successfully")
                            st.json(payload)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"Migration completed: {payload}"
                            })

                        # -------- DELETION --------
                        elif any(k in payload for k in ["Dashboard_name", "dashboard_name", "resource_id"]):

                            st.success("🗑️ Dashboard Deleted Successfully")
                            st.json(payload)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"Deleted: {payload}"
                            })

                        # -------- COMPARISON --------
                        elif "status" in payload and "counts" in payload["status"]:

                            stats = payload["status"]["counts"]

                            st.info("⚖️ Dashboard Comparison Result")

                            st.markdown(f"""
                            <div style="
                                background:#1e293b;
                                padding:15px;
                                border-radius:10px;
                                border:1px solid #334155;
                            ">
                                <p>📊 <b>Dev Total:</b> {stats.get('dev_total')}</p>
                                <p>📊 <b>Prod Total:</b> {stats.get('prod_total')}</p>
                                <p>❌ <b>Missing in Prod:</b> {stats.get('missing_in_prod')}</p>
                                <p>❌ <b>Missing in Dev:</b> {stats.get('missing_in_dev')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"""
Dev: {stats.get('dev_total')}
Prod: {stats.get('prod_total')}
Missing in Prod: {stats.get('missing_in_prod')}
Missing in Dev: {stats.get('missing_in_dev')}
"""
                            })

                        # -------- GENERIC SUCCESS --------
                        else:
                            st.success("✅ Operation completed")
                            st.json(payload)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": str(payload)
                            })

                    # ❌ FAILURE
                    else:
                        st.error("❌ Operation failed")
                        st.json(data)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": str(data)
                        })

                # ======================================================
                # ✅ CASE 2: LANGGRAPH / CHAT RESPONSE
                # ======================================================
                elif isinstance(data, dict) and "messages" in data:

                    content = data["messages"][-1].get("content", "")

                    st.markdown(content)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": content
                    })

                # ======================================================
                # ✅ CASE 3: FALLBACK
                # ======================================================
                else:

                    content = data.get("response", str(data))

                    st.markdown(content)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": content
                    })

                st.session_state.processing = False
                st.rerun()

            except requests.exceptions.Timeout:
                st.error("⏰ Request timed out")
                st.session_state.processing = False

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.processing = False