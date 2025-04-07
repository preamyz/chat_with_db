import streamlit as st
import pandas as pd
import google.generativeai as genai

st.title("Chat with Database")
st.subheader("Interactive Conversation with Data to Reveal Insights")

# Gemini API Key #
model = None
try:
    genai.configure(api_key="AIzaSyDWgnaByVSYbq-bpBHcJnYsMSHLrZSv_HA")
    model = genai.GenerativeModel("gemini-1.5-flash")
    st.success("✅ Gemini model is ready!")
except Exception as e:
    st.error(f"Failed to configure Gemini: {e}")

# Session State #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "csv_data" not in st.session_state:
    st.session_state.csv_data = None

# Upload Files #
st.subheader("Browse Your Data")

data_file = st.file_uploader("Upload dataset (in csv format)", type="csv")

if data_file:
    try:
        st.session_state.csv_data = pd.read_csv(data_file)
        st.success("✅ Data loaded")
        st.dataframe(st.session_state.csv_data.head())
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

# Chat History #
for role, msg in st.session_state.chat_history:
    st.chat_message(role).markdown(msg)

# Chat Input #
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
            example_record = df.head(2).to_string()

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

**Sample Data (Top 2 Rows):**
{example_record}

Output only the code. No explanation.
"""

            response = model.generate_content(prompt)
            code = response.text.strip("```python").strip("```").strip()

            st.write("🧾 **Generated Code:**")
            st.code(code, language="python")

            if "ANSWER" not in code:
                st.error("❌ Generated code does not contain 'ANSWER'.")
            else:
                try:
                    local_vars = {"df": df}
                    exec(code, local_vars)
                    ANSWER = local_vars.get("ANSWER", "No variable named ANSWER was found.")
                    st.success("✅ Code executed successfully.")
                    st.write("🧾 **Result (ANSWER):**")
                    st.write(ANSWER)

                    # Explain Result #
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
