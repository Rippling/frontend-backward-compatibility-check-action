FROM python:3.6.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY git-actions-frontend-backward-compatibility git-actions-frontend-backward-compatibility
CMD ["python", "git-actions-frontend-backward-compatibility/scripts/process_open_prs_for_frontend.py"]