# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9.5

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV PORT=8080

EXPOSE 8080

CMD [ "python", "manage.py", "runserver", "-h", "0.0.0.0", "-p", "8080"]