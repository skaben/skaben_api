import time
import json
import logging

from typing import Union, Optional
from kombu.mixins import ConsumerProducerMixin
from kombu.message import Message

from skaben.config import get_settings
from skaben.modules.mq.config import MQConfig
from skaben.modules.mq.interface import MQInterface

from skaben.modules.core.devices import SmartDeviceEnum, DeviceEnum

settings = get_settings()


class MessageHandler(ConsumerProducerMixin, MQInterface):
    """MQ Message handler class"""

    def __init__(self, config: MQConfig):
        super(MQInterface).__init__(config)

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

            if parsed.get("device_type") in [e.value for e in SmartDeviceEnum]:
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
    def parse_basic(routing_key: list) -> dict:
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


'''
class SaveConfigHandler(MessageHandler):
    """Save handler"""

    def device_not_found(self, device_type: str, device_uid: str):
        """spawn notification about unregistered device"""
        raise NotImplementedError

    def handle_message(self, body: Union[str, dict], message: Message):
        """handling server update message

           save device state to database without sending update packet (CUP) back
           serializer context {"no_send": True} do the trick
        """
        parsed = super().handle_message(body, message)
        logging.debug(f'handling {body} {message}')
        message.ack()

        _type = parsed['device_type']
        _uid = parsed['device_uid']
        # include timestamp to load
        parsed['datahold'].update({"timestamp": parsed.get('timestamp', int(time.time()))})
        if _type not in [e.value for e in SmartDeviceEnum]:
            logging.error(f'device type {_type} is not supported')
            return
        # TODO: сопоставление типа девайса с моделью и схемой, сохранение через них в БД


class SendConfigHandler(MessageHandler):
    """send config update to clients (CUP)"""

    def handle_message(self, body: Union[str, dict], message: Message):
        parsed = super().handle_message(body, message)
        device_type = parsed.get('device_type')
        device_uid = parsed.get('device_uid')
        message.ack()

        try:
            if device_type in [e.value for e in DeviceEnum]:
                return self.send_config_simple(device_type, device_uid)
            # достаем из базы актуальный конфиг устройства
            config = self.get_config(device_type, device_uid)
            # проверяем разницу хэшей в пришедшем конфиге и серверном
            if str(config.get('hash')) != str(parsed.get('hash', '')):
                self.send_config(device_type, device_uid, config)
            else:
                # обновляем таймстемп в любом случае
                self.update_timestamp_only(parsed)
        except Exception as e:
            raise Exception(f"{body} {message} {parsed} {e}")

    def get_config(self, device_type: str, device_uid: str) -> dict:
        device = self.smart.get(device_type)
        if not device:
            self.report_error(f"device not in smart list, but CUP received: {device_type}")
            return {}

        try:
            device_instance = device['model'].objects.get(uid=device_uid)
            serializer = device['serializer'](instance=device_instance)
            return serializer.data
        except Exception as e:  # DoesNotExist - fixme: make normal exception
            self.report_error(f"[DB error] {device_type} {device_uid}: {e}")

    def send_config(self, device_type: str, device_uid: str, config: dict):
        logging.debug(f'sending config for {device_type} {device_uid}')
        packet = CUP(
            topic=device_type,
            uid=device_uid,
            task_id=get_task_id(device_uid[-4:]),
            datahold=config,
            timestamp=int(time.time())
        )
        self._publish(packet.payload,
                      exchange=self.config.exchanges.get('mqtt'),
                      routing_key=f"{device_type}.{device_uid}.cup")

    @staticmethod
    def get_scl_config():
        borders = get_borders()
        last_counter = get_last_counter()
        if last_counter > borders[-1]:
            last_counter = borders[-1]
        elif last_counter < borders[0]:
            last_counter = borders[0]

        device_uid = 'all'
        datahold = {
            'borders': borders,
            'level': last_counter,
            'state': 'green'
        }
        return device_uid, datahold

    def send_config_simple(self, device_type: str, device_uid: Optional[str] = None):
        """Отправляем конфиг простым устройствам в соответствии с текущим уровнем тревоги"""
        datahold = {}

        if device_type != 'scl':
            state_id = get_current_alert_state()
            instance = SimpleConfig.objects.filter(dev_type=device_type, state__id=state_id).first()
            if not device_uid or device_type in ('pwr', 'hold'):
                device_uid = 'all'
            if not instance or not instance.config:
                return

            datahold = instance.config

        if device_type == 'scl':
            device_uid, datahold = self.get_scl_config()

        packet = CUP(
            topic=device_type,
            uid=device_uid,
            datahold=datahold,
            task_id='simple',
            timestamp=int(time.time())
        )

        self.publish(packet.payload,
                     exchange=self.exchanges.get('mqtt'),
                     routing_key=f"{device_type}.{device_uid}.cup")
'''