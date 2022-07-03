import time
import json
import logging

from typing import Union, Optional
from kombu.mixins import ConsumerProducerMixin
from kombu.message import Message

from skaben.config import get_settings
from skaben.modules.mq.config import MQConfig
from skaben.modules.mq.interface import MQInterface

settings = get_settings()


class BaseWorker(ConsumerProducerMixin, MQInterface):
    """Worker base class"""

    def __init__(self, config: MQConfig):
        super(MQInterface).__init__(config=config, limited=settings.amqp.limited)

    def handle_message(self, body: Union[str, dict], message: Message) -> dict:
        """parse MQTT message to dict or return untouched if it's already dict
           only messages which comes with 'ask.*' routing key should be parsed
        """
        rk = message.delivery_info.get('routing_key').split('.')
        if rk[0] == 'ask':
            try:
                rk = rk[1:]
            except Exception as e:
                raise Exception(f"cannot parse routing key `{rk}` >> {e}")

            try:
                parsed = self.parse_basic(rk)
                data = self.parse_json(body)
            except Exception as e:
                raise Exception(f"cannot parse message payload `{body}` >> {e}")

            if parsed.get("device_type") in ['lock', 'terminal']:
                parsed.update(self.parse_smart(data))
            else:
                parsed.update(**data)
                if not parsed.get('timestamp'):
                    parsed['timestamp'] = data.get('datahold', {}).get('timestamp', 1)
            return parsed
        else:
            return body  # just return already parsed message

    @staticmethod
    def parse_json(json_data: Optional[str] = None) -> dict:
        """get dict from json"""
        try:
            if isinstance(json_data, dict):
                return json_data
            if not json_data:
                return {}
            return json.loads(json_data)
        except Exception as exc:
            logging.error(f'cannot parse json: {json_data} {exc}')
            return {}

    @staticmethod
    def parse_basic(routing_key: str) -> dict:
        """get device parameters from topic name (routing key)"""
        device_type, device_uid, command = routing_key
        data = dict(device_type=device_type,
                    device_uid=device_uid,
                    command=command)
        return data

    def parse_smart(self, data: dict) -> dict:
        """get additional data-fields from smart device"""
        parsed = {'datahold': f'{data}'}
        if isinstance(data, dict):
            datahold = self.parse_json(data.get('datahold', {}))
            parsed = dict(
                timestamp=int(data.get('timestamp', 0)),
                task_id=data.get('task_id', 0),
                datahold=datahold,
                hash=data.get('hash', '')
            )
        return parsed

    def update_timestamp_only(self, parsed: dict, timestamp: Union[str, int] = None):
        timestamp = int(time.time()) if not timestamp else timestamp
        parsed.update({
            'timestamp': timestamp,
            'datahold': {'timestamp': timestamp},
            'command': 'sup',
            'hash': parsed.get('hash', '')
        })
        self.save_device_config(parsed)

    def push_device_config(self, parsed: dict):
        """send config to device (emulates config request from device'"""
        routing_key = f"{parsed['device_type']}.{parsed['device_uid']}.cup"
        self._publish(parsed,
                      exchange=self.config.exchanges.get('ask'),
                      routing_key=routing_key)

    def save_device_config(self, payload: dict):
        """Сохранить конфигурацию устройства"""
        payload.update({"timestamp": int(time.time())})
        kwargs = {
            "body": payload,
            "exchange": self.config.exchanges.get('internal'),
            "routing_key": 'save'
        }
        self._publish(**kwargs)

    def get_consumers(self, consumer, channel):
        """setup consumer and assign callback"""
        _consumer = consumer(queues=self.config.queues.values(),
                             accept=['json'],
                             callbacks=[self.handle_message])
        return [_consumer]

    def __str__(self):
        return f"{self.__class__.__name__}"
