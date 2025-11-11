# Dockerfile CORRETO para Python
FROM python:3.11-slim
WORKDIR /app

# 1. Copia o manifesto de dependências
COPY requirements.txt .

# 2. Instala as dependências Python (pyzmq)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia o código-fonte
COPY server.py .
# (Se houver outros arquivos Python, use COPY . .)
RUN mkdir -p data
RUN pip install pyzmq

# 4. Define o comando de execução
CMD ["python", "server.py"]