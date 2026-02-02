from typing import List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class CocktailInfo(BaseModel):
    alcohol_content: str = Field(..., description='鸡尾酒的酒精度')
    texture: str = Field(..., description="鸡尾酒的口感, 例如：清爽")
    recommendation: str = Field(...,description="推荐这杯鸡尾酒的理由")

class Question(BaseModel):
    """当客人描述鸡尾酒需求不清晰的时候调用."""
    question: str = Field(
        description="向客户提问的一个问题,在客户对描述的鸡尾酒不清晰的时候,用来澄清客户的需求"
    )

class BartenderState(TypedDict):
    final_recommendation: Annotated[CocktailInfo,"鸡尾酒信息"]
    messages: Annotated[list[AnyMessage], add_messages]
