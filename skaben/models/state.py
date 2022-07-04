from skaben.models.base import Base
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, DateTime, Boolean


class AlertCounter(Base):
    """Цифровой уровень тревоги"""

    value = Column(Integer, default=0)
    comment = Column(String(256), default='changed by system')
    timestamp = Column(DateTime(timezone=False), server_default=func.now())

    def __str__(self):
        return f'{self.value} {self.comment} at {self.timestamp}'


class State(Base):
    """Глобальный уровень состояния системы"""

    name = Column(String(32), nullable=False, unique=True)
    order = Column(Integer, nullable=False, unique=True)
    info = Column(String(256))
    threshold = Column(Integer, default=-1)
    current = Column(Boolean, default=False)
    counter_mod = Column(Integer, default=5)

    @property
    def is_ingame(self):
        """В игре ли статус"""
        return self.threshold >= 0
