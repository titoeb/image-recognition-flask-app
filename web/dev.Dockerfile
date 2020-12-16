FROM python:3.7

WORKDIR /usr/web

COPY requirements.txt ./ 

RUN pip install -r requirements.txt

ENV FLASK_APP=app.py

ENV FLASK_ENV=development

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
