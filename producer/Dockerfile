FROM python:3.9-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

# O uvicorn irá rodar na porta 8000 e estará acessível a partir de qualquer IP no container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]