FROM python:3.10
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt update && apt install -y libffi-dev libnacl-dev python3-dev && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME [ "/data" ]

COPY . ./

ENV DISCORD_BOT_CONFIG=/data/config.yaml DISCORD_BOT_LOGFILE=/data/discord.log DISCORD_BOT_ENV=/data/.env

CMD ["bash", "./docker-entrypoint.sh"]
