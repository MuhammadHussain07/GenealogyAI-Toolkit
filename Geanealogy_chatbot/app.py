import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Cohere
from langchain.chains import RetrievalQA
from langchain_cohere import CohereEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import base64
import os

# Load environment variables
load_dotenv()
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
PDF_FILE = os.getenv('PDF_FILE_PATH')

class GenealogyBot:
    def __init__(self):
        self.pdf_documents = None
        self.qa_chain = None
        self.chat_history = []
        self.vector_store = None
        
        # Sample timeline data
        self.timeline_data = pd.DataFrame({
            'date': ['1899-06-13', '1917-04-12', '1919-07-14', '1964-04-08'],
            'event': ['Born in Abbot Town, Maine', 
                     'Enlisted in U.S. Navy',
                     'Honorably discharged from Navy',
                     'Passed away in Boise'],
            'category': ['Birth', 'Military', 'Military', 'Death'],
            'end_date': ['1899-06-13', '1917-04-12', '1919-07-14', '1964-04-08']
        })
        
    def load_pdf(self):
        """Load and process the PDF file"""
        try:
            if not PDF_FILE:
                raise ValueError("PDF file path not configured")
            
            loader = PyPDFLoader(PDF_FILE)
            self.pdf_documents = loader.load()
            
            # Initialize embeddings and vector store with specific model
            embeddings = CohereEmbeddings(
                cohere_api_key=COHERE_API_KEY,
                model="embed-english-v3.0",  # Specify the model name
            )
            texts = [doc.page_content for doc in self.pdf_documents]
            self.vector_store = FAISS.from_texts(texts, embeddings)
            
            # Initialize LLM and QA chain
            llm = Cohere(
                cohere_api_key=COHERE_API_KEY,
                model="command"  # Specify the model for text generation
            )
            
            prompt_template = """Use the following pieces of context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            {context}
            
            Question: {question}
            Answer: """
            
            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(),
                chain_type_kwargs={"prompt": PROMPT}
            )
            
            return True
        except Exception as e:
            st.error(f"Error loading PDF: {e}")
            return False

    def create_family_tree(self):
        """Create family tree using Plotly"""
        fig = go.Figure()
        
        # Define node positions
        nodes = {
            'WFD': {'x': 0, 'y': 0, 'name': 'William F. Dunn Sr.\n(1899-1964)'},
            'FWD': {'x': -1, 'y': 1, 'name': 'Franklin W. Dunn\n(Father)'},
            'CF': {'x': 1, 'y': 1, 'name': 'Carolyn French\n(Mother)'}
        }
        
        # Add nodes
        for node_id, info in nodes.items():
            fig.add_trace(go.Scatter(
                x=[info['x']], 
                y=[info['y']],
                mode='markers+text',
                name=node_id,
                text=[info['name']],
                textposition='bottom center',
                marker=dict(size=30, color='lightblue'),
                showlegend=False
            ))
        
        # Add lines for relationships
        for child, parents in {'WFD': ['FWD', 'CF']}.items():
            child_pos = nodes[child]
            for parent in parents:
                parent_pos = nodes[parent]
                fig.add_trace(go.Scatter(
                    x=[child_pos['x'], parent_pos['x']],
                    y=[child_pos['y'], parent_pos['y']],
                    mode='lines',
                    line=dict(color='black'),
                    showlegend=False
                ))
        
        fig.update_layout(
            title='Family Tree',
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig

    def create_timeline(self):
        """Create interactive timeline using Plotly"""
        fig = px.timeline(
            self.timeline_data,
            x_start='date',
            x_end='end_date',
            y='category',
            color='category',
            text='event',
            title='Life Timeline'
        )
        
        fig.update_layout(
            xaxis_title='',
            yaxis_title='',
            height=400
        )
        
        return fig

    def get_response(self, query):
        """Get response for user query"""
        try:
            if not self.qa_chain:
                return "System is not properly initialized. Please try again."
            
            response = self.qa_chain({"query": query})
            return response['result']
        except Exception as e:
            return f"Error processing query: {e}"

def display_chat_interface():
    st.title("Chat with Biography Assistant 👨‍👩‍👧‍👦")
    
    # Initialize bot if needed
    if not st.session_state.bot.qa_chain:  # Changed condition to check qa_chain
        if st.session_state.bot.load_pdf():
            st.success("Biography loaded successfully!")
        else:
            st.error("Failed to load biography")
            return

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about William F. Dunn Sr..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = st.session_state.bot.get_response(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def display_family_tree():
    st.title("Family Tree Visualization")
    
    # Visualization options
    col1, col2 = st.columns(2)
    with col1:
        theme = st.selectbox("Color Theme", ["Blue", "Green", "Sepia"])
    with col2:
        layout = st.selectbox("Layout", ["Standard", "Hierarchical"])
    
    # Generate and display tree using Plotly
    fig = st.session_state.bot.create_family_tree()
    st.plotly_chart(fig, use_container_width=True)

def display_timeline():
    st.title("Life Timeline")
    
    # Timeline options
    view_type = st.selectbox("View Type", ["Chronological", "Categories"])
    
    # Generate and display timeline
    fig = st.session_state.bot.create_timeline()
    st.plotly_chart(fig, use_container_width=True)

def display_documents():
    st.title("Historical Documents")
    
    # Document viewer
    if st.session_state.bot.pdf_documents:
        st.write("Biography Content:")
        for i, page in enumerate(st.session_state.bot.pdf_documents):
            with st.expander(f"Page {i+1}"):
                st.write(page.page_content)

def main():
    st.set_page_config(
        page_title="William F. Dunn Sr. Biography Assistant",
        page_icon="👨‍👩‍👧‍👦",
        layout="wide"
    )
    
    # Initialize session state
    if 'bot' not in st.session_state:
        st.session_state.bot = GenealogyBot()
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Chat", "Family Tree", "Timeline", "Documents"])
    
    # Display selected page
    if page == "Chat":
        display_chat_interface()
    elif page == "Family Tree":
        display_family_tree()
    elif page == "Timeline":
        display_timeline()
    elif page == "Documents":
        display_documents()

if __name__ == "__main__":
    main()