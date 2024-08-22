import os
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.memory import ChatMessageHistory
from langchain.agents.agent_toolkits import (
    create_vectorstore_agent,
    VectorStoreToolkit,
    VectorStoreInfo
)
from unstructured.file_utils.filetype import EXT_TO_FILETYPE, FileType
from typing import List
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent
from langchain.agents import AgentType

langchain.verbose = True

def create_index() -> VectorStoreIndexWrapper:
    from unstructured.file_utils.filetype import EXT_TO_FILETYPE, FileType

    EXT_TO_FILETYPE[".py"] = FileType.TXT

    # すべてのファイルタイプをインデックスに含める
    loader = DirectoryLoader("./src/", glob="**/*.*")
    return VectorstoreIndexCreator().from_loaders([loader])

# Indexをもとにtoolを作成
def create_tools(index: VectorStoreIndexWrapper) -> List[BaseTool]:
    vectorstore_info = VectorStoreInfo(
        name="gbkr_rag_slack",
        description="Source code and other files in gbkr_rag_slack",
        vectorstore=index.vectorstore
    )
    toolkit = VectorStoreToolkit(vectorstore_info=vectorstore_info)
    return toolkit.get_tools()

def chat(
    message: str, history: ChatMessageHistory, index: VectorStoreIndexWrapper
) -> str:
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    tools = create_tools(index)
    
    memory = ConversationBufferMemory(chat_memory=history, memory_key="chat_history", return_messages=True)
    
    agent_chain = initialize_agent(
        tools,
        llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory
    )
    
    # 入力メッセージに基づいてファイルの情報を検索し、応答を生成
    return agent_chain.run(input=message)
