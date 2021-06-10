FROM python:3.6.10-slim-buster
RUN apt-get update -y && apt-get install -y jq

CMD ["python", "/deployment_scripts/process_open_prs_for_frontend.py"]