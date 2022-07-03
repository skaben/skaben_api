from sqlalchemy import func
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects import postgresql


class DeviceMixin(object):
    """Device mixin"""

    # информация об устройстве
    name = Column(String(256), default='')
    # тип устройства
    device_type = Column(String(128), nullable=False)
    # MAC-адрес устройства в сети
    device_addr = Column(postgresql.MACADDR, nullable=True)
    # время последней регистрации
    timestamp = Column(DateTime(), server_default=func.now())
    # исключение из общей рассылки управляющих сообщений
    ignored = Column(Boolean, default=False)
