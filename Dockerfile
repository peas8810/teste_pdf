FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y libreoffice python3-pip && \
    apt-get clean

WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt

CMD ["python3", "app.py"]

