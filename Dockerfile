FROM python:3.10-alpine3.17 as builder

RUN python3 -m venv /app
RUN /app/bin/pip install -U pip

COPY requirements.txt /mnt/
RUN /app/bin/pip install -Ur /mnt/requirements.txt

FROM python:3.10-alpine3.17 as builder

WORKDIR /app

COPY . /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

COPY run_migrations.sh /app/
RUN chmod +x /app/run_migrations.sh

CMD ["/app/run_migrations.sh"]
