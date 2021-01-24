FROM python:3.8

RUN mkdir /squire

WORKDIR /squire

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "launcher.py"]