FROM python:3.8-slim

RUN mkdir /squire
RUN mkdir /squire/logs

WORKDIR /squire

RUN apt-get update && apt-get install libffi-dev libnacl-dev python3-dev -y

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "launcher.py"]