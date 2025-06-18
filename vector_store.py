import os
from langchain_community.vectorstores import Chroma
from config import VECTOR_STORE_PATH, COLLECTION_NAME, OPENAI_EMBEDDINGS_MODEL
from data_splitters import split_markdown_data, split_pdf_data


def get_vector_store_global():
    if os.path.exists(VECTOR_STORE_PATH):
        return Chroma(
            persist_directory=VECTOR_STORE_PATH,
            collection_name=COLLECTION_NAME,
            embedding_function=OPENAI_EMBEDDINGS_MODEL,
        )
    else:
        loader = split_markdown_data()
        docs = loader.load()
        return Chroma.from_documents(
            documents=docs,
            embedding=OPENAI_EMBEDDINGS_MODEL,
            persist_directory=VECTOR_STORE_PATH,
            collection_name=COLLECTION_NAME,
        )


def get_vector_store_temp(pdf_path):
    doc = split_pdf_data(pdf_path)
    return Chroma.from_documents(documents=doc, embedding=OPENAI_EMBEDDINGS_MODEL)