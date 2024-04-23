import os
from langchain import OpenAI
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st
import pickle
import time
from openai.error import RateLimitError

from dotenv import load_dotenv
load_dotenv()  #не забудьте взять вставить апи кей 

st.title("Research tool Aizel")
st.sidebar.title("Ссылки на статьи")

if 'urls' not in st.session_state:
    st.session_state.urls = [''] 

for i, url in enumerate(st.session_state.urls):
    st.sidebar.text_input(f"URL {i+1}", value=url, key=f"url_input_{i}")

if st.sidebar.button("Добавить ссылку"):
    st.session_state.urls.append('')
    st.experimental_rerun()

process_url_clicked = st.sidebar.button("Загрузить")
file_path = "faiss_store_openai.pkl"

main_placeholder = st.empty()
llm = OpenAI(temperature=0.9, max_tokens=500)

if process_url_clicked:
    # загружаем и делим дату
    loader = UnstructuredURLLoader(urls=urls)
    main_placeholder.text("Загружается дата")
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000
    )
    main_placeholder.text("Делим текст")
    docs = text_splitter.split_documents(data)
 #создал эмбеддинги и сахарнил в файл
    embeddings = OpenAIEmbeddings()
    vectorstore_openai = FAISS.from_documents(docs, embeddings)
    main_placeholder.text("Ембеддинг вектор билдится")
    time.sleep(4)

    with open(file_path, "wb") as f:
        pickle.dump(vectorstore_openai, f)

query = main_placeholder.text_input("Вопрос на английском: ")
if query:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            vectorstore = pickle.load(f)
            chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=vectorstore.as_retriever())
            try:
                result = chain({"question": query}, return_only_outputs=True)
            except RateLimitError:
                st.error("API rate limit exceeded. Please try again later.")
                #это на всякий случай
                time.sleep(10)  # Retry after 10 seconds
                result = chain({"question": query}, return_only_outputs=True)
            st.header("Answer")
            st.write(result["answer"])
            #показываем соурсы 
            sources = result.get("sources", "")
            if sources:
                st.subheader("Sources:")
                sources_list = sources.split("\n")  
                for source in sources_list:
                    st.write(source)
