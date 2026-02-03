import operator
from typing import List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class CocktailInfo(BaseModel):
    """当信息足够，进行推荐的时候调用."""
    name: str = Field(..., description='鸡尾酒的英文名称')
    cn_name: str = Field(..., description='鸡尾酒的中文名称')
    description: str = Field(..., description='一段富有诗意、简短的鸡尾酒描述')
    alcohol_content: str = Field(..., description='鸡尾酒的酒精度')
    texture: str = Field(..., description="鸡尾酒的口感, 例如：清爽")
    recommendation: str = Field(...,description="推荐这杯鸡尾酒的理由")

class Question(BaseModel):
    """当客人描述鸡尾酒需求不清晰以及了解客人偏好的时候调用."""
    question: str = Field(
        description="向客户提问的一个问题,在客户对描述的鸡尾酒不清晰的时候,用来澄清客户的需求"
    )
class ExtractRequirements(BaseModel):
    """从客人的描述中提取出鸡尾酒的需求."""
    key_words: str = Field(
        description="需求类别,例如：酒精度、口感等"
    )
    requirements: str = Field(
        description="从客人的描述中提取出的具体的需求,例如：酒精度为50%，口感为清爽"
    )

class BartenderState(TypedDict):
    origin_input: Annotated[str, "客人原始输入"]
    user_requirements: Annotated[list[str], "客人的需求描述", operator.add]
    final_recommendation: Annotated[CocktailInfo,"鸡尾酒信息"]
    messages: Annotated[list[AnyMessage], add_messages]
