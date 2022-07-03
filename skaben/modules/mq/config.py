import kombu
import logging
from kombu import Connection, Exchange, Queue

from skaben.config import get_settings

settings = get_settings()
kombu.disable_insecure_serializers(allowed=['json'])


class MQFactory:

    @staticmethod
    def create_queue(queue_name: str, exchange: Exchange, is_topic: bool = True, **kwargs) -> Queue:
        routing_key = f'#.{queue_name}' if is_topic else queue_name
        return Queue(
            queue_name,
            durable=False,
            exchange=exchange,
            routing_key=routing_key,
            **kwargs
        )

    @staticmethod
    def create_exchange(channel, name: str, type: str = "topic"):
        exchange = Exchange(name, type=type)
        bound_exchange = exchange(channel)
        bound_exchange.declare()
        return bound_exchange


class MQConfig:

    exchanges: dict
    queues: dict

    def __init__(self, amqp_url: str):
        self.conn = Connection(amqp_url)
        self.pool = self.conn.ChannelPool()

    def init_mqtt_exchange(self) -> dict:
        """Initialize MQTT exchange infrastructure"""
        logging.info('initializing mqtt exchange')
        with self.pool.acquire(timeout=settings.amqp_timeout) as channel:
            # main mqtt exchange, used for messaging out.
            # note that all replies from clients starts with 'ask.' routing key goes to ask exchange
            self.exchanges.update(mqtt=MQFactory.create_exchange(channel, 'mqtt'))
        return self.exchanges

    def init_ask_exchange(self) -> dict:
        logging.info('initializing mqtt replies (ask) exchange')
        if not self.exchanges.get('mqtt'):
            self.init_mqtt_exchange()

        with self.pool.acquire(timeout=settings.amqp_timeout) as channel:
            ask_exchange = MQFactory.create_exchange(channel, 'ask')
            ask_exchange.bind_to(exchange=self.exchanges['mqtt'],
                                 routing_key='ask.#',
                                 channel=channel)
            self.exchanges.update(ask=ask_exchange)
        return self.exchanges

    def init_internal_exchange(self):
        """Initializing internal direct exchange"""
        logging.info('initializing internal exchange')
        with self.pool.acquire(timeout=settings.amqp_timeout) as channel:
            exchange = MQFactory.create_exchange(channel, 'internal', 'direct')
            self.exchanges.update(internal=exchange)
        return self.exchanges

    def init_transport_queues(self) -> dict:
        exchange = self.exchanges.get('ask')
        if not exchange:
            self.init_ask_exchange()

        q_names = [
            'cup',
            'sup',
            'info',
            'ack',
            'nack',
            'pong'
        ]
        queues = {name: MQFactory.create_queue(name, exchange) for name in q_names}
        self.queues.update(**queues)
        return self.queues

    def init_internal_queues(self) -> dict:
        exchange = self.exchanges.get('internal')
        if not exchange:
            self.init_internal_exchange()

        q_names = [
            'log',
            'errors',
            'save'
        ]
        queues = {name: MQFactory.create_queue(name, exchange, is_topic=False) for name in q_names}
        self.queues.update(**queues)
        return self.queues


if not settings.amqp.url:
    logging.error('AMQP settings is missing, exchanges will not be initialized')
    mq_config = None
else:
    mq_config = MQConfig(settings.amqp.url)
