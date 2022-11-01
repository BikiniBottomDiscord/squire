FROM python:3.8-slim

RUN mkdir /squire
RUN mkdir /squire/logs

WORKDIR /squire

#RUN apt-get update && apt-get install -y libopus0 opus-tools libffi-dev libnacl-dev python3-dev
RUN apt-get update && apt-get install -y git

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "launcher.py"]