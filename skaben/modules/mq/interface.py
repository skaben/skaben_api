import time
import traceback
from typing import Union

from skaben.modules.mq.config import MQConfig


class MQInterface:

    def __init__(self, config: MQConfig, limited: bool):
        self.config = config
        self.config.init_mqtt_exchange()
        if not limited:
            self.config.init_transport_queues()
            self.config.init_internal_queues()

    def send_mqtt_skaben(self, topic: str, uid: str, command: str, payload = None):
        """Отправить в MQTT команду SKABEN"""
        data = {"timestamp": int(time.time())}
        if payload:
            data["datahold"] = payload
        self.send_mqtt_raw(f"{topic}.{uid}.{command}", data)

    def send_mqtt_raw(self, topic: str, message: Union[str, dict]):
        """Отправить команду в MQTT"""
        try:
            kwargs = {
                "body": message,
                "exchange": self.config.exchanges.get('mqtt'),
                "routing_key": f"{topic}"
            }
            self._publish(**kwargs)
        except Exception:
            raise Exception(f"{traceback.format_exc()}")

    def _publish(self, body: dict, exchange: str, routing_key: str):
        with self.config.pool.acquire() as channel:
            prod = self.config.conn.Producer(channel)
            prod.publish(
                body,
                exchange=exchange,
                routing_key=routing_key,
                retry=True
            )
