import typer
from skaben.modules.mq.recurrent import mq_app
from skaben.config import get_settings

settings = get_settings()

app = typer.Typer()
app.add_typer(mq_app, name="mq")


@app.command()
def show():
    """show config"""
    typer.echo(f'{settings}')


if __name__ == "__main__":
    app()

