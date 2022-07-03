import typer
import logging
app = typer.Typer()


@app.command()
def run_workers():
    """start pinger"""
    logging.info('Starting pinger')


if __name__ == "__main__":
    app()

