# Recursive Sales Data Q&A Engine

Ever looked at a massive sales CSV and wished you could just ask it a question?  
This app makes that possible.

Built with Streamlit and Pandas, this tool lets you type natural language questions like:

> “What are the top-selling products by revenue in each store?”

It then:
- Detects whether the question is complex or atomic
- Breaks it down into simpler sub-questions if needed
- Resolves each part using actual Python code
- Returns the final answer along with reasoning and logs

---

## Features

- Automatic question decomposition
- Data analysis using Pandas
- Understands store, product, category, and time-based queries
- Shows step-by-step reasoning and logs
- Clean and interactive Streamlit interface
