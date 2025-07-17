from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

def create_vector_store(docs, metadata):
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(docs, embeddings)
    db.add_metadata(metadata)
    return db
