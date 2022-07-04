from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from skaben.helpers import convert_to_optional


class AlertCounterSchema(BaseModel):
    """Цифровой уровень тревоги"""

    value: int | None = 0
    comment: str | None = 'changed by system'
    timestamp: datetime | None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "value": 100,
                "comment": "изменен мастером игры",
                "timestamp": datetime.now()
            }
        }


class StateSchema(BaseModel):
    """Глобальный уровень состояния системы"""

    order: int
    name: str
    info: str
    threshold: int | None = -1
    current: bool | None = False
    counter_mod: int | None = 5

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "order": 1,
                "name": "green",
                "info": "стандартное состояние",
                "threshold": 150,
                "counter_mod": 10,
                "current": True
            }
        }


class StateUpdateSchema(BaseModel):
    __annotations__ = convert_to_optional(StateSchema)


class ResponseStateSchema(StateSchema):
    """Схема состояния с uuid"""

    uuid: str | UUID
