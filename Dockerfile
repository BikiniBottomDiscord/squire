FROM python:3.8

RUN mkdir /squire

WORKDIR /squire

RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "launcher.py"]