import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY")

OPENAI_EMBEDDINGS_MODEL = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
VECTOR_STORE_PATH = "vector_store"
COLLECTION_NAME = "credito_habitacao"