FROM python:latest
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
RUN mkdir log res data 2> /dev/null
COPY . .
EXPOSE 6974
ENV PYTHONPATH=/app/src
CMD ["python3", "src/server/server.py"]
