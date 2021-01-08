FROM python:2
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip --no-cache-dir install -r requirements.txt

CMD ["python", "main.py"]