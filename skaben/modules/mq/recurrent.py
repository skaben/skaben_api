import time
import typer
import logging

from skabenproto.packets import PING

from skaben.config import get_settings
from skaben.modules.mq.interface import MQInterface
from skaben.modules.mq.config import get_mq_config
from skaben.modules.core.devices import DeviceEnum, SmartDeviceEnum

settings = get_settings()
mq_config = get_mq_config()

mq_app = typer.Typer()


@mq_app.command(name="ping")
def ping_devices():
    running = True
    interface = MQInterface(mq_config)
    topics = [e.value for e in DeviceEnum] + [e.value for e in SmartDeviceEnum]
    message = f'[+] start pinger with interval {settings.amqp.timeout} for topics: {", ".join(topics)}'
    typer.echo(message)
    logging.info(message)
    while running:
        for topic in topics:
            packet = PING(topic, timestamp=int(time.time()))
            interface.send_mqtt_skaben(packet)
        time.sleep(settings.amqp.timeout)
