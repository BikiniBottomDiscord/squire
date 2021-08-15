FROM python:3.8-slim

RUN mkdir /squire
RUN mkdir /squire/logs

WORKDIR /squire

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "launcher.py"]