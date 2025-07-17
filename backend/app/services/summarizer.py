from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI

def generate_summary(docs):
    chain = load_summarize_chain(OpenAI(temperature=0.2), chain_type="map_reduce")
    return chain.run(docs)
