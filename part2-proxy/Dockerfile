
FROM python:3.10
WORKDIR /app
COPY proxy.py .
RUN pip install pyzmq
CMD ["python", "proxy.py"]
