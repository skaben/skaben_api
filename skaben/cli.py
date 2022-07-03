import os
import sys
import typer
import logging

from skaben.config import get_settings
from skaben.modules.mq.interface import MQInterface

app = typer.Typer()
settings = get_settings()


@app.command()
def test():
    """test command"""
    handler = MQInterface()
    typer.echo(f'Get handler {handler}')


@app.command()
def show():
    """show config"""
    typer.echo(f'{settings}')


if __name__ == "__main__":
    app()

