import pandas as pd
import PyPDF2
import streamlit as st
from fuzzywuzzy import fuzz
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Cohere
from langchain.chains import RetrievalQA
from langchain_cohere import CohereEmbeddings
from langchain.schema import Document

# File paths
csv_file = "D:/proj/Geanealogy_chatbot/Fiverr Anthony Updated Spread Sheet.csv"
pdf_file = "D:/proj/Geanealogy_chatbot/images_data.pdf"
cohere_api_key = "paste the api here"

# Load CSV data
def load_csv_data():
    try:
        data = pd.read_csv(csv_file, encoding="Windows-1252")
        return data
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

csv_data = load_csv_data()

# Extract text from PDF using PyPDFLoader
def extract_documents_with_pypdfloader(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        if not documents:
            st.error("PDF documents list is empty. Check the PDF file or parsing logic.")
        return documents
    except Exception as e:
        st.error(f"Error loading documents with PyPDFLoader: {e}")
        return []

pdf_documents = extract_documents_with_pypdfloader(pdf_file)

# Create LangChain retriever for PDF content
def create_pdf_retriever(pdf_documents):
    if not pdf_documents:
        return None

    embeddings = CohereEmbeddings(model="large", cohere_api_key=cohere_api_key)
    db = FAISS.from_documents(pdf_documents, embeddings)
    retriever_chain = RetrievalQA.from_chain_type(
        llm=Cohere(model="command", cohere_api_key=cohere_api_key),
        retriever=db.as_retriever(),
        return_source_documents=True
    )
    return retriever_chain

pdf_retriever = create_pdf_retriever(pdf_documents)

# Extract all rows related to a specific ancestor from the CSV
def get_ancestor_data(ancestor_name):
    if csv_data is None:
        return "CSV data is not loaded."

    # Extract the summary (first row)
    summary_data = csv_data.iloc[0].to_dict()

    # Extract detailed data for the ancestor
    details = []
    for index, row in csv_data.iterrows():
        if isinstance(row["ï»¿Ancestor Name"], str) and ancestor_name.lower() in row["ï»¿Ancestor Name"].lower():
            details.append(row.to_dict())

    # Combine summary and detailed data
    return {"Summary": summary_data, "Details": details} if details else None

# Query the data for a specific ancestor in the CSV
def query_csv(query):
    ancestor_name = query.split("data of")[-1].strip()
    data = get_ancestor_data(ancestor_name)

    if not data:
        return f"No data found for {ancestor_name}."

    # Format the output
    summary = "\n".join([f"{key}: {value}" for key, value in data["Summary"].items() if pd.notna(value)])
    details = "\n".join([
        f"{row['ï»¿Ancestor Name']}\n" + "\n".join([f"{key}: {value}" for key, value in row.items() if pd.notna(value)])
        for row in data["Details"]
    ])

    return f"Summary:\n{summary}\n\nDetails:\n{details}"

# Query the PDF using LangChain retriever
def query_pdf(query):
    if pdf_retriever is not None:
        try:
            response = pdf_retriever.invoke({"query": query})
            if response:
                result = response["result"]
                source_docs = response["source_documents"]
                sources = "\n".join([doc.metadata.get("source", "Unknown source") for doc in source_docs])
                return f"Answer: {result}\nSources: {sources}"
        except Exception as e:
            st.error(f"Error querying PDF with LangChain: {e}")
            return None
    else:
        return "PDF retriever is not available."

# Unified query handler
def query_handler(query):
    if "data of" in query.lower():
        csv_result = query_csv(query)
        pdf_result = query_pdf(query)

        if csv_result and pdf_result:
            return f"CSV Result:\n{csv_result}\n\nPDF Result:\n{pdf_result}"
        elif csv_result:
            return f"CSV Result:\n{csv_result}"
        elif pdf_result:
            return f"PDF Result:\n{pdf_result}"
        else:
            return "No matching data found."
    else:
        return "Please ask about a specific ancestor's data in the format: 'I need a full table data of <Ancestor Name>'."

# Streamlit app
st.title("Genealogy Chatbot")
st.sidebar.title("Options")

# Query input
query = st.text_input("Ask a question about the genealogy data:")

if query:
    st.info(f"Your Query: {query}")
    response = query_handler(query)
    st.success(response)
