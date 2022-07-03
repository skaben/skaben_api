FROM python:3.10-slim-buster as builder

ENV PYTHONUBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PYTHONDONTWRITEBYTECODE=1

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip

FROM builder as final

ENV PYTHONPATH="/opt/app/skaben"
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

EXPOSE 80 443 8080

CMD ["sh", "-c", "/opt/app/entrypoint.sh"]
