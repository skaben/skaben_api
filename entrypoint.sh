#!/usr/bin/env bash

alembic upgrade head &&
uvicorn skaben.main:app \
	--host 0.0.0.0 \
	--port 8080 \
      	--lifespan=on \
	--use-colors \
	--loop uvloop \
	--http httptools \
     	--reload \
	--log-level debug
