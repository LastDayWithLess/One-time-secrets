FROM python:3.12

WORKDIR /prodject

COPY ./requirements.txt /prodject/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /prodject/requirements.txt

COPY ./app /prodject/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]