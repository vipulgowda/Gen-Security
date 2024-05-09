from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

llm = GoogleGenerativeAI(model="gemini-pro",temperature=0)

def summarize(path):
    loader = GenericLoader.from_filesystem(
            path,
            glob="*",
            suffixes=[".py"],
            show_progress=True,
            parser=LanguageParser(),
    )
    docs = loader.load()

    prompt1 = PromptTemplate.from_template(
        """
            Summarize the python code and check for any malicious code and state in UPPERCASE and its effects.
        {text}
        """)

    chain = (
      {"text": RunnablePassthrough()} 
      | prompt1
      | llm
      | StrOutputParser()
    )
    output = "\n".join([d.page_content for d in docs])
    result = chain.invoke(output)
    return(result)

print("Welcome to my code summarizer.  Give me a path to a Package program and I'll summarize it.")

while True:
    try:
        line = input("llm>> ")
        if line:
            result = summarize(line)
            print(result)
        else:
            break
    except Exception as e:
        print(e)
        break