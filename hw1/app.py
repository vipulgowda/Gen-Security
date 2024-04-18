from bs4 import BeautifulSoup
import sys
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain import hub
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader


# Define available options as a dictionary
options = {
    "1": { "link":"company/culture/all-remote/", "title": "Remote Culture"},
    "2": { "link":"company/culture/inclusion/" ,"title": "Culture and Inclusion"},
    "3": { "link":"company/working-groups/" ,"title": "Working Groups"},
    "4": { "link":"about/migration-reports/" ,"title": "Migration reports"},
    "5": { "link":"engineering/architecture/" ,"title": "Architecture"},
    "6": { "link":"engineering/development/analytics/" ,"title":"Analytics" },
    "7": { "link":"engineering/development/dev/create" ,"title": "Engineering Development"},
    "8": { "link":"engineering/development/incubation/" ,"title": "Incubation"},
    "9": { "link":"engineering/development/sec/govern/" ,"title": "Security and Governance"},
    "10": { "link":"engineering/careers/matrix/development/" ,"title":"Careers" },
    "11": { "link":"engineering/readmes/" ,"title": "Team Members"},
    "12": { "link":"engineering/infrastructure/core-platform/systems/" ,"title":"Infrastructure- Core Platform" },
    "13": { "link":"engineering/infrastructure/engineering-productivity/" ,"title": "Engineering Productivity" },
    "14": { "link":"communication/" ,"title": "Communication"},
    "15": { "link":"hiring/" ,"title": "Hiring" },
    "16": { "link":"business-technology/data-team/" ,"title":"Data Team" },
    "17": { "link":"leadership/" ,"title": "Leadership"},
    "18": { "link":"developer-relations/technical-marketing/" ,"title": "Technical Marketing"},
    "19": { "link":"marketing/project-management-guidelines/" ,"title": "Marketing Project Guidelines" },
    "20": { "link":"exit" ,"title": "Exit"}
}

# Print available options
print("Welcome to Gitlab Handbook")
print("Please select the domain you want to explore")
for key, value in options.items():
  title = value["title"]
  print(f"{key}. {title}")

# Get user input for option selection
choice = input("Enter option number: ")

# Validate choice and print selected option text
if choice in options:
  if choice == "20":
    print("Exiting program.")
    sys.exit(1)
  else:
    print(f"You selected: {options[choice]['title']}")
else:
  print("Invalid choice.")
  print("Exiting program.")
  sys.exit(1)

#Select the link of selected option
selected_option = options[choice]['link']
url = f'https://handbook.gitlab.com/handbook/{selected_option}'

#Initialize the vector Store
vectorstore = Chroma(
    embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query"),
    persist_directory=".chromadb"
)

print("Please wait. This might take few minutes to load")
print(f'While you wait, you can explore the questions you want to ask from {url}')

def load_docs(docs):
    """
    Loads documents into a vector store for efficient processing.

    Args:
      docs (list): A list of documents, where each document is a string.

    Raises:
      ValueError: If the input `docs` is not a list.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=10)
    splits = text_splitter.split_documents(docs)
    vectorstore.add_documents(documents=splits)


loader = RecursiveUrlLoader(
    url=url, max_depth=2, extractor=lambda x: BeautifulSoup(x, "html.parser").text
)

load_docs(loader.load())

retriever = vectorstore.as_retriever()

prompt = hub.pull("rlm/rag-prompt")

llm = GoogleGenerativeAI(model="gemini-pro")

def format_docs(docs):
    """Formats a list of documents into a single string with double newlines between documents.

    Args:
        docs: A list of dictionaries, where each dictionary represents a document
                and has a "page_content" key containing the document text.

    Returns:
        A string containing the formatted document content.
    """
    # Extract page content from each document and join them with double newlines
    formatted_text =  "\n\n".join(doc.page_content for doc in docs)
    return formatted_text

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("Welcome to my RAG application.  Ask me a question and I will answer it from the documents in my database shown below")

# Iterate over documents and dump metadata
document_data_sources = set()
for doc_metadata in retriever.vectorstore.get()['metadatas']:
    document_data_sources.add(doc_metadata['source']) 
for doc in document_data_sources:
    print(f"  {doc}")

while True:
    line = input("llm>> ")
    if line:
        result = rag_chain.invoke(line)
        print(result)
    else:
        break
