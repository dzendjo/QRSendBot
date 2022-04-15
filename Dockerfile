FROM ubuntu:20.04

COPY requirements.txt /opt/

RUN apt-get update -y
RUN apt-get install libzbar0 -y
RUN apt-get install python3 python3-pip -y
# RUN pip install --upgrade pip
RUN pip install -r /opt/requirements.txt --no-use-pep517 --no-cache-dir -q --compile

COPY app/ /opt/app/

WORKDIR /opt/app

CMD ["python3", "engine.py"]