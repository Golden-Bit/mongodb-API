# Usa l'immagine base di Ubuntu 22.04
FROM ubuntu:22.04

# Imposta il maintainer (facoltativo)
LABEL maintainer="tuo_nome@example.com"

# Imposta non-interattivo per evitare richieste di configurazione manuale
ENV DEBIAN_FRONTEND=noninteractive

# Imposta il fuso orario
ENV TZ=Europe/Rome

# Aggiorna i pacchetti e installa dipendenze di base
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    wget \
    gnupg \
    curl \
    lsb-release \
    ca-certificates \
    tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Scarica e installa manualmente libssl1.1 da Ubuntu 20.04 (focal)
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb && \
    dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb && \
    rm libssl1.1_1.1.1f-1ubuntu2_amd64.deb

# Aggiungi il repository di MongoDB
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Installa MongoDB
RUN apt-get update && apt-get install -y mongodb-org && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Scarica dockerize dal link fornito e imposta i permessi di esecuzione
RUN wget https://github.com/jwilder/dockerize/releases/download/v0.8.0/dockerize-alpine-linux-amd64-v0.8.0.tar.gz && \
    tar -xvzf dockerize-alpine-linux-amd64-v0.8.0.tar.gz && \
    mv dockerize /usr/local/bin/dockerize && \
    chmod +x /usr/local/bin/dockerize && \
    rm dockerize-alpine-linux-amd64-v0.8.0.tar.gz

# Crea la directory per MongoDB
RUN mkdir -p /data/db
VOLUME /data/db

# Imposta la directory di lavoro per l'app
WORKDIR /app

# Copia il file requirements.txt e installa le dipendenze
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia il contenuto della directory 'app' nel container
COPY ./app /app

# Espone la porta per FastAPI
EXPOSE 8094

# Avvia MongoDB e l'applicazione FastAPI, con Dockerize per attendere che MongoDB sia pronto
CMD ["dockerize", "-wait", "tcp://localhost:27017", "-timeout", "30s", "bash", "-c", "mongod --bind_ip_all & uvicorn main:app --host 0.0.0.0 --port 8094"]
