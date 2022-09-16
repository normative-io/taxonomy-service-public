ARG PYTHON_VERSION

FROM "python:${PYTHON_VERSION}"

RUN apt-get update && \
    apt-get install -y jq

RUN pip3 install --upgrade pip
RUN pip3 install pipenv
COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --ignore-pipfile

COPY . /opt/taxonomysearch
WORKDIR /opt/taxonomysearch

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=application.py

ENTRYPOINT ["flask", "run", "--host=0.0.0.0", "--port=80"]
