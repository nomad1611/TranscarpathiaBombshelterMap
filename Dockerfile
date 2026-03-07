FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1\
	PIP_NO_CACHE_DIR=1 \
	POETRY_VIRTUALENVS_CREATE=false \
	POETRY_VERSION=2.0.1

WORKDIR /app
RUN apt-get update && apt-get install -y \
build-essential \ 
&& rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY . /app/
EXPOSE 8501
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

ENV STREAMLIT_GATHER_USAGE_STATS=false
CMD ["streamlit", "run", "src/1_🏠︎_Main.py"]
