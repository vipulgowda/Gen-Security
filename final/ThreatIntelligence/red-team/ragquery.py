from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import chromadb
import os
import readline
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold


llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, safety_settings={ HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,})  

# Define embedding function
embedding_function = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query")

# Open vector database
current_directory = f"{os.path.dirname(__file__)}"
chroma_db = os.path.join(current_directory, f"{current_directory}/.chromadb")

persistent_client = chromadb.PersistentClient(path=chroma_db)
db = Chroma(
    client=persistent_client,
    collection_name="groups_collection",
    embedding_function=embedding_function,
)
db.get()
retriever = db.as_retriever(search_kwargs={"k":20})

# Instantiate LLM and QA chain
from langchain.chains.question_answering import load_qa_chain
# llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest")
#llm = GoogleGenerativeAI(model="gemini-pro")
chain = load_qa_chain(llm, chain_type="stuff")

def perform_query(retriever, chain, query):
    relevant_docs = retriever.invoke(query)
    results = chain.invoke({'input_documents':relevant_docs, 'question':query})
    return(results['output_text'])

print("Welcome to my Mitre ATT&CK Q&A application.  Type a query and I'll answer it based on the latest data. Example:\n List the commands used T1040 - Network Sniffing and explain all the platforms that I can run the command in. ")
while True:
    line = input("llm>> ")
    try:
        if line:
            print(perform_query(retriever, chain, line))
        else:
            break
    except:
        print()

# Perform query by retrieving context and invoking chain
# line = """What threat actors sent phishing messages to their targets?"""
# line = """What threat actors sent messages to their targets over social media accounts?"""
# line = "What are some phishing techniques used by threat actors?"
# line = "What techniques does APT 28 utilize?"
