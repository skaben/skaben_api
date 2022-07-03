from sqlalchemy import Column, Integer, Boolean
from skaben.models import Base
from skaben.models.mixins import DeviceMixin


class Lock(DeviceMixin, Base):
    """Lock device class"""

    closed = Column(Boolean, default=True)
    blocked = Column(Boolean, default=False)
    sound = Column(Boolean, default=True)
    timer = Column(Integer, default=10)
