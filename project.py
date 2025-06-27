# STEP 1: Import Libraries

import pandas as pd
import streamlit as st
from typing import List, Dict, Any
import re
import json

# STEP 2: Load & Clean Data

@st.cache_data
def load_data():
    sales_data = pd.read_csv("Demo Sales Data.xlsx.csv")
    sales_data['Total Retail'] = sales_data['Total Retail'].str.replace(',', '').astype(float)
    sales_data['Profit'] = sales_data['Profit'].str.replace(',', '').astype(float)
    sales_data['Department'].fillna("Unknown", inplace=True)

    if 'Date' not in sales_data.columns:
        sales_data['Date'] = pd.date_range(start='2023-01-01', periods=len(sales_data), freq='D')

    return sales_data

sales_data = load_data()

# STEP 3: Define Helper Functions

def is_complex_question(question: str) -> bool:
    complex_keywords = ["compare", "trend", "top", "each", "across", "average", "by", "from", "to", "increase", "decrease"]
    return any(kw in question.lower() for kw in complex_keywords)

def decompose_question(question: str) -> List[str]:
    if "compare" in question.lower() and "across" in question.lower():
        return [
            "What is the revenue trend of dairy products in City A?",
            "What is the revenue trend of dairy products in City B?"
        ]
    elif "top-selling products by revenue in each store" in question.lower():
        stores = sales_data['Store Name'].unique()
        return [f"What are the top-selling products by revenue in {store}?" for store in stores]
    else:
        return [question]

def resolve_atomic_question(q: str) -> Dict[str, Any]:
    q_lower = q.lower()
    answer = ""
    reasoning = ""

    if "highest revenue in q1 2023" in q_lower:
        df = sales_data.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        q1_data = df[(df['Date'].dt.month >= 1) & (df['Date'].dt.month <= 3) & (df['Date'].dt.year == 2023)]
        result = q1_data.groupby('Department')['Total Retail'].sum().sort_values(ascending=False)
        top = result.idxmax()
        value = result.max()
        answer = top
        reasoning = f"Filtered for Q1 2023 and calculated revenue per department. {top} had {value:.2f}"

    elif "top-selling products by revenue in" in q_lower:
        store = re.findall(r"in (.*?)\?", q)
        if store:
            store_name = store[0].strip()
            df = sales_data[sales_data['Store Name'].str.strip() == store_name]
            top_products = df.groupby('Description')['Total Retail'].sum().sort_values(ascending=False).head(3)
            answer = top_products.to_dict()
            reasoning = f"Grouped sales in {store_name} and selected top 3 by revenue."

    elif "highest average basket size in march 2023" in q_lower:
        df = sales_data.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        march_data = df[(df['Date'].dt.month == 3) & (df['Date'].dt.year == 2023)]
        avg_basket = march_data.groupby('Store Name')['Total Retail'].mean().sort_values(ascending=False)
        answer = avg_basket.idxmax()
        reasoning = f"Computed average basket size in March 2023 per store. {answer} had the highest."

    elif "sales increase or decrease for beverages from january to june 2023" in q_lower:
        df = sales_data.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        jan_data = df[(df['Date'].dt.month == 1) & (df['Date'].dt.year == 2023) & (df['Department'].str.lower().str.contains("beverage"))]
        jun_data = df[(df['Date'].dt.month == 6) & (df['Date'].dt.year == 2023) & (df['Department'].str.lower().str.contains("beverage"))]
        jan_total = jan_data['Total Retail'].sum()
        jun_total = jun_data['Total Retail'].sum()

        if jun_total > jan_total:
            answer = "Sales increased"
        elif jun_total < jan_total:
            answer = "Sales decreased"
        else:
            answer = "Sales remained constant"

        reasoning = f"Compared total beverage sales in Jan 2023 ({jan_total:.2f}) and Jun 2023 ({jun_total:.2f})."

    else:
        answer = "Cannot resolve"
        reasoning = "Need more advanced NLP parsing."

    return {"question": q, "answer": answer, "reasoning": reasoning}

def aggregate_answers(answers: List[Dict[str, Any]]) -> str:
    if len(answers) == 1:
        return answers[0]['answer']
    return json.dumps({a['question']: a['answer'] for a in answers}, indent=2)


# STEP 4: Recursive Pipeline

def recursive_question_answerer(question: str) -> Dict[str, Any]:
    state = {
        "original_question": question,
        "pending_subquestions": [],
        "answered_subquestions": [],
        "logs": []
    }

    complex_flag = is_complex_question(question)
    state['logs'].append(f"Complexity check: {'complex' if complex_flag else 'atomic'}")

    if complex_flag:
        subs = decompose_question(question)
        state['pending_subquestions'].extend(subs)
    else:
        state['pending_subquestions'].append(question)

    while state['pending_subquestions']:
        q = state['pending_subquestions'].pop(0)
        res = resolve_atomic_question(q)
        state['answered_subquestions'].append(res)
        state['logs'].append(f"Answered: {q} -> {res['answer']}")

    final_answer = aggregate_answers(state['answered_subquestions'])
    state['final_answer'] = final_answer
    return state


# STEP 5: Streamlit UI

st.set_page_config(page_title="Recursive Sales Question Answerer", layout="wide")
st.title("🧠 Recursive Sales Data Q&A")

query = st.text_input("Ask a question about the sales data:", placeholder="e.g., What are the top-selling products by revenue in each store?")

if st.button("Submit") and query:
    output = recursive_question_answerer(query)
    st.subheader("Final Answer")
    st.success(output['final_answer'])

    with st.expander("🔍 Question Breakdown & Reasoning"):
        for item in output['answered_subquestions']:
            st.markdown(f"**Q:** {item['question']}\n\n**A:** {item['answer']}\n\n*Reasoning:* {item['reasoning']}")

    with st.expander("📜 Logs"):
        for log in output['logs']:
            st.text(log)
