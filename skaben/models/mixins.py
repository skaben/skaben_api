from sqlalchemy import func
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects import postgresql


class DeviceMixin(object):
    """Device mixin"""

    # подробная информация об устройстве
    info = Column(String(512), default='')
    # адрес устройства в сети
    ipaddr = Column(postgresql.INET, nullable=True)
    # время последней регистрации
    timestamp = Column(DateTime(), server_default=func.now())
    # исключение из общей рассылки управляющих сообщений
    ignored = Column(Boolean, default=False)
