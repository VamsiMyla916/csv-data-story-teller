import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import matplotlib.pyplot as plt
import seaborn as sns
import re # Import the regular expressions library for cleaning

# --- Page Configuration ---
st.set_page_config(
    page_title="CSV Data Storyteller",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialize Session State ---
# This is crucial to store the results and prevent them from disappearing
if 'insights' not in st.session_state:
    st.session_state.insights = None
if 'visualization_code' not in st.session_state:
    st.session_state.visualization_code = None
if 'visualization_fig' not in st.session_state:
    st.session_state.visualization_fig = None


# --- Functions ---
def configure_genai():
    """Configures the Generative AI model with the API key from Streamlit secrets."""
    try:
        # Securely load the API key from Streamlit's secrets manager
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return True
    except KeyError:
        st.error("GEMINI_API_KEY not found in secrets. Please add it to continue.")
        st.info("Refer to the README for instructions on how to set up your API key securely.")
        return False
    except Exception as e:
        st.error(f"An error occurred during API configuration: {e}")
        return False


# --- Main Application ---

# Title and Description
st.title("📊 CSV Data Storyteller")
st.markdown("""
Welcome to the CSV Data Storyteller! This app helps you understand your data without needing to be a data scientist.
Upload your CSV file, and our AI assistant will provide a high-level summary, actionable business insights, and even suggest a custom visualization.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Upload Your Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        if st.button("Clear All Results"):
            st.session_state.insights = None
            st.session_state.visualization_code = None
            st.session_state.visualization_fig = None
            st.rerun()

    st.header("2. About")
    st.info("This app uses Google's Gemini API to generate insights and visualizations. Your data is not stored after the analysis is complete.")


# --- Core Logic ---
if uploaded_file is not None:
    st.header("Your Data Preview")
    try:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())

        # --- Action Buttons ---
        st.subheader("What do you want to do?")
        
        if st.button("Generate Insights ✨"):
            if configure_genai():
                model = genai.GenerativeModel('gemini-pro-latest')
                
                buffer = io.StringIO()
                df.info(buf=buffer)
                df_info = buffer.getvalue()

                prompt = f"""
                You are an expert data analyst. Based on the following summary of a CSV file, provide a high-level summary and three actionable business insights.
                **Dataframe Head (First 5 Rows):**\n{df.head().to_string()}
                **Dataframe Info:**\n{df_info}
                **Dataframe Description:**\n{df.describe().to_string()}
                ---
                Please provide the following in Markdown format:
                1.  **High-Level Summary:** Describe the dataset's structure, quality, and potential purpose.
                2.  **Three Actionable Business Insights:** Provide three distinct, creative insights a business user could act upon.
                """
                
                with st.spinner("Our AI is analyzing your data..."):
                    response = model.generate_content(prompt)
                    st.session_state.insights = response.text
                    st.rerun()

        if st.button("Suggest a Visualization 📈"):
            if configure_genai():
                model = genai.GenerativeModel('gemini-pro-latest')
                
                vis_prompt = f"""
                You are an expert data visualization specialist. Your task is to generate a single block of Python code to create the most insightful chart possible for the given dataset.
                **CRITICAL INSTRUCTIONS:**
                1.  **Analyze the Data First:** Look at the number of rows and data types.
                2.  **Choose the RIGHT Chart Type:** For small datasets (under 50 rows), strongly prefer simple charts like bar plots or scatter plots. Avoid complex or time-series plots unless the data clearly supports it.
                3.  **Code Requirements:** The dataset is in a pandas DataFrame named `df`. Use Matplotlib or Seaborn. The final plot object must be assigned to a variable named `fig`. The code must be a single, self-contained block, ready to execute. **DO NOT** include any explanation or markdown backticks.
                Here is the data summary:
                - Number of rows: {len(df)}
                - Columns: {df.columns.to_list()}
                - First 5 rows:\n{df.head().to_string()}
                """
                
                with st.spinner("AI is crafting a visualization..."):
                    response = model.generate_content(vis_prompt)
                    raw_code = response.text
                    
                    code_match = re.search(r"```python\n(.*?)```", raw_code, re.DOTALL)
                    code_to_execute = code_match.group(1) if code_match else raw_code.strip()

                    st.session_state.visualization_code = code_to_execute
                    
                    scope = {'df': df, 'plt': plt, 'sns': sns, 'io': io}
                    fig, ax = plt.subplots()
                    scope['fig'] = fig
                    scope['ax'] = ax
                    
                    exec(code_to_execute, scope)
                    st.session_state.visualization_fig = scope['fig']
                    st.rerun()

        st.divider()

        # --- Display Results from Session State ---
        if st.session_state.insights:
            st.header("AI-Powered Analysis Report 📈")
            st.markdown(st.session_state.insights)

        if st.session_state.visualization_fig:
            st.header("AI-Suggested Visualization")
            st.pyplot(st.session_state.visualization_fig)
        
        if st.session_state.visualization_code:
            with st.expander("Click to see the code that generated the plot"):
                st.code(st.session_state.visualization_code, language="python")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Awaiting for CSV file to be uploaded.")

