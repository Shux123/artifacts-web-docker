# Dockerfile

FROM python:3.13.3-slim-bullseye

RUN apt-get update && \
    apt-get upgrade --yes

RUN useradd --create-home shux
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
USER shux
WORKDIR /home/shux

ENV VIRTUALENV=/home/shux/venv
RUN python3 -m venv $VIRTUALENV
ENV PATH="$VIRTUALENV/bin:$PATH"

COPY --chown=shux requirements.txt ./
RUN python -m pip install --upgrade pip setuptools && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=shux artifacts.py ./
COPY --chown=shux config.py ./
COPY --chown=shux app/ app/

ENTRYPOINT ["entrypoint.sh"]

CMD ["gunicorn", "artifacts:flask_app",  '--bind', '0.0.0.0:8000']