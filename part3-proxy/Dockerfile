FROM python:3.11-slim
WORKDIR /app
COPY proxy.py .
RUN pip install pyzmq
CMD ["python", "proxy.py"]
