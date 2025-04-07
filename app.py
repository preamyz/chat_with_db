import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="🤖 Chat with Your Data", layout="wide")
st.title("🤖 Chat with Your Data | AI-Powered Insights, Data Driven by Gemini")
st.caption("Upload your dataset and data dictionary, then ask questions — Gemini will will give natural language insights!")

# -------- Gemini Config -------- #
model = None
try:
    genai.configure(api_key="AIzaSyCycIJ35pKnWIY8391m2FZB5mzh2UncVtA")
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    st.success("✅ Gemini model is ready!")
except Exception as e:
    st.error(f"Failed to configure Gemini: {e}")

# -------- Session State -------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "csv_data" not in st.session_state:
    st.session_state.csv_data = None
if "data_dict" not in st.session_state:
    st.session_state.data_dict = None

# -------- Upload Files -------- #
st.subheader("📁 Upload Your Files")
col1, col2 = st.columns(2)

with col1:
    data_file = st.file_uploader("Upload main dataset (e.g. transactions.csv)", type="csv")
    if data_file:
        try:
            st.session_state.csv_data = pd.read_csv(data_file)
            st.success("✅ Data loaded")
            st.dataframe(st.session_state.csv_data.head())
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")

with col2:
    dict_file = st.file_uploader("Upload Data Dictionary (optional)", type="csv")
    if dict_file:
        try:
            st.session_state.data_dict = pd.read_csv(dict_file)
            st.success("✅ Data Dictionary loaded")
            st.dataframe(st.session_state.data_dict.head())
        except Exception as e:
            st.error(f"❌ Failed to read data dictionary: {e}")

# -------- Chat History -------- #
for role, msg in st.session_state.chat_history:
    st.chat_message(role).markdown(msg)

# -------- Chat Input -------- #
if user_input := st.chat_input("Ask your question about the data..."):

    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    if not model:
        st.warning("Please configure Gemini first.")
    elif st.session_state.csv_data is None:
        st.warning("Please upload a dataset first.")
    else:
        try:
            df_name = "df"
            df = st.session_state.csv_data
            question = user_input
            data_dict_text = (
                st.session_state.data_dict.to_string()
                if st.session_state.data_dict is not None
                else "No data dictionary provided."
            )
            example_record = st.session_state.csv_data.head(2).to_string()

            prompt = f"""
You are a helpful Python code generator.
Your job is to write Python code snippets based on the user's question and the provided DataFrame information.

Please generate Python code that:
- uses a DataFrame named `{df_name}`
- stores the result in a variable called `ANSWER`
- does NOT import pandas
- changes date columns to datetime if needed
- uses exec() to run the code

Here’s the context:

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

Output only the code. No explanation.
"""

            response = model.generate_content(prompt)
            code = response.text.strip("```python").strip("```").strip()

            # execute the generated code
            try:
                local_vars = {"df": df}
                exec(code, local_vars)
                ANSWER = local_vars.get("ANSWER", "No variable named ANSWER was found.")
                st.success("✅ Code executed successfully.")
                st.write("🧾 **Result (ANSWER):**")
                st.write(ANSWER)

                # -------- Explain Result -------- #
                explain_the_results = f'''
The user asked: "{question}"  
Here is the result: {ANSWER}  
Please summarize this answer and provide your interpretation.  
Include your opinion on the customer's persona or behavior based on the result.
'''
                explanation_response = model.generate_content(explain_the_results)
                explanation = explanation_response.text

                st.write("🧠 **Gemini's Explanation:**")
                st.markdown(explanation)

            except Exception as exec_error:
                st.error(f"⚠️ Error running generated code: {exec_error}")

            st.session_state.chat_history.append(("assistant", f"Answer: {ANSWER}"))

        except Exception as e:
            st.error(f"❌ Error generating response: {e}")
