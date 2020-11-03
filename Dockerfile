FROM python:3.8

RUN mkdir /squire

WORKDIR /squire

COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "launcher.py"]