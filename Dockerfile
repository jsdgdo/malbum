FROM python:3.12

ENV PYTHONBUFFERED=1

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y sqlite3 dos2unix

COPY . .

COPY entrypoint.sh /code/
RUN chmod +x /code/entrypoint.sh
RUN dos2unix /code/entrypoint.sh && apt-get --purge remove -y dos2unix && rm -rf /var/lib/apt/lists/*

EXPOSE 8080

ENTRYPOINT ["/code/entrypoint.sh"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8080"]