from core.config import USE_OPENAI, OPENAI_API_KEY, HUGGINGFACE_MODEL_NAME, HUGGINGFACEHUB_API_TOKEN
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
import os

class DocumentQA:
    def __init__(self, index_path="data/vectorstore/index"):
        self.index_path = index_path
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.embeddings = self._load_embeddings()
        self.llm = self._load_llm()

    def _load_embeddings(self):
        if USE_OPENAI:
            return OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        else:
            return HuggingFaceEmbeddings(model_name=HUGGINGFACE_MODEL_NAME)

    def _load_llm(self):
        if USE_OPENAI:
            if not OPENAI_API_KEY:
                raise ValueError("USE_OPENAI is true but OPENAI_API_KEY is not set. Please set OPENAI_API_KEY in environment variables or .env file.")
            return ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        else:
            # 使用 HuggingFace 本地模型或 API
            try:
                if HUGGINGFACEHUB_API_TOKEN:
                    return HuggingFaceEndpoint(
                        repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
                        huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
                        temperature=0.1
                    )
                else:
                    # 如果没有 API token，使用本地模型
                    from langchain_community.llms import HuggingFacePipeline
                    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                    import torch
                    
                    model_id = "gpt2"  # 使用较小的模型用于演示
                    tokenizer = AutoTokenizer.from_pretrained(model_id)
                    model = AutoModelForCausalLM.from_pretrained(model_id)
                    pipe = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=tokenizer,
                        max_new_tokens=100,
                        temperature=0.1
                    )
                    return HuggingFacePipeline(pipeline=pipe)
            except Exception as e:
                # 如果加载 HuggingFace 模型失败，抛出错误
                raise ValueError(f"Failed to load HuggingFace model: {str(e)}. Please either set OPENAI_API_KEY or HUGGINGFACEHUB_API_TOKEN.")

    def load_and_index_pdf(self, file_path):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(documents)

        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        self.vectorstore.save_local(self.index_path)
        self.retriever = self.vectorstore.as_retriever()
        self.qa_chain = RetrievalQA.from_chain_type(llm=self.llm, retriever=self.retriever)

    def load_existing_index(self):
        if os.path.exists(self.index_path):
            self.vectorstore = FAISS.load_local(self.index_path, self.embeddings)
            self.retriever = self.vectorstore.as_retriever()
            self.qa_chain = RetrievalQA.from_chain_type(llm=self.llm, retriever=self.retriever)
            return True
        return False

    def ask(self, question):
        if not self.qa_chain:
            raise ValueError("Index not loaded. Please load documents first.")
        return self.qa_chain.invoke({"query": question})
