FROM python:3
LABEL maintainer="Joakim Ellestad <95db6b89@gmail.com>"

WORKDIR /usr/src/app

COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/ .

CMD [ "python", "./update_dns.py"]

