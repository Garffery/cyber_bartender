from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

BARTENDER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一名经验丰富的酒保,请根据客人的心情,要求推荐一杯合适的鸡尾酒,鸡尾酒的配方可以在网上进行检索"),
    MessagesPlaceholder(variable_name="messages"),
])