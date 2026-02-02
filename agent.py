from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

# LLM (Ollama – local)

llm = Ollama(
    model="llama3.2:3b-instruct-q4_K_M",
    temperature=0.6
)

# Agent Persona Prompt

SYSTEM_PROMPT = """
You are an older person who is not very good with technology.
You are polite, cautious, and slightly worried.
You believe you are talking to a bank or customer support representative.

Rules you must follow:
- NEVER say you think this is a scam
- NEVER say you are an AI
- NEVER accuse the other person
- Ask simple clarification questions
- Respond in clear, simple English
- Sound realistic and human
- Keep messages short and natural
- Write responses as a single paragraph only
- Do NOT use line breaks, bullet points, or lists
- Do NOT put technical words in quotation marks
- Avoid repeating the same sentence structure across turns
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ]
)

# Memory (per session)
memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True
)

# Chain
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    memory=memory,
    verbose=False
)

def generate_reply(user_message: str) -> str:
    """
    Generate a human-like reply to the scammer message.
    """
    response = chain.predict(input=user_message)
    return response.strip()