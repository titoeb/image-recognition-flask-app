FROM python:3.8

WORKDIR /usr/web

COPY ./ ./

COPY requirements.txt ./

RUN pip install -r requirements.txt

ENV FLASK_APP=app.py

CMD ["flask", "run", "--host=0.0.0.0"]
