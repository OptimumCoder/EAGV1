# models.py
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import json

class PerceptionType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    SENSOR = "sensor"

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class BaseModelWithJSON(BaseModel):
    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        return json.loads(json.dumps(d, cls=DateTimeEncoder))
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PerceptionType: lambda v: v.value if isinstance(v, PerceptionType) else str(v)
        }

class Perception(BaseModelWithJSON):
    input_type: PerceptionType
    content: str
    metadata: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)  # Add timestamp field

    @field_validator('input_type')
    def validate_perception_type(cls, v):
        if isinstance(v, PerceptionType):
            return v
        if isinstance(v, str):
            return PerceptionType(v)
        raise ValueError(f'Invalid perception type: {v}')

class LLMResponse(BaseModelWithJSON):
    content: str
    metadata: Dict
    timestamp: datetime = Field(default_factory=datetime.now)

class Memory(BaseModelWithJSON):
    id: str
    content: str
    context: Dict
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    importance_score: float = Field(ge=0, le=1)

class Decision(BaseModelWithJSON):
    id: str
    context: Dict
    options: List[str]
    selected_option: str
    confidence_score: float = Field(ge=0, le=1)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Action(BaseModelWithJSON):
    id: str
    action_type: str
    parameters: Dict
    status: str = "pending"
    result: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)