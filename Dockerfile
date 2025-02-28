FROM python:3.12-alpine
LABEL maintainer="solopdev.com"

ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
        fi && \
    rm -rf /tmp

COPY ./app /app
EXPOSE 8080

RUN adduser --disabled-password --no-create-home user

USER user
