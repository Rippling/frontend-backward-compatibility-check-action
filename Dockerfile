FROM python:3.6.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY scripts scripts/
CMD ["python", "scripts/process_open_prs_for_frontend.py"]