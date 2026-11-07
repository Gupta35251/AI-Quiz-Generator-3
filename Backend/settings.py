from pydantic import BaseModel,Field,field_validator
from typing import List,Dict,Optional,Annotated,Literal

class User(BaseModel):
    content:str
    no_of_questions:Annotated[int,Field(default=5,gt=0,description="Give the no of questions you want the agent ask from you")]
    level:Annotated[str,Field(default="medium",description="Select the difficulty level from easy,medium,hard")]

    @field_validator("level")
    @classmethod
    def level_validation(cls,value):
        available_levels = ["easy","medium","hard"]
        if value.lower() not in available_levels:
            raise ValueError("Enter correct level")
        return value.lower()

class Question(BaseModel):
    id: Optional[str] = None
    question: str
    concept: str
    type: Literal["mcq", "multiple_answer", "code", "theory"]
    options: Optional[List[str]] = None
    answer: List[str]
    description: str
    difficulty: Literal["easy", "medium", "hard"]

class Quiz(BaseModel):
    topic:str
    questions:List[Question]


class userAnswer(BaseModel):
    question:str
    user_answer:List[str]

class Evaluation(BaseModel):
    question:str
    user_answer:List[str]
    correct_answer:List[str]
    is_correct:bool
    description:str

class QuizResult(BaseModel):
    question:str
    is_correct:bool
    user_answer:List[str]
    correct_answer:List[str]
    description:str

# user_info = {"content":"str","no_of_questions":10,"level":"easy"}
# user1 = User(**user_info)
# def check(user:User):
#     print(user.content)
#     print(user.no_of_questions)
#     print(user.level)
