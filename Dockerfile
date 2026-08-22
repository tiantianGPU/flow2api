FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    ALLOW_DOCKER_HEADED_CAPTCHA=true \
    DISPLAY=:99 \
    PERSONAL_BROWSER_HEADLESS=0 \
    PLAYWRIGHT_BROWSERS_PATH=0 \
    AGENT_CAPTCHA_MODULE_PATH=/app/reg-factory

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl ffmpeg fonts-liberation libasound2 \
        libatk-bridge2.0-0 libatk1.0-0 libcups2 libdrm2 libgbm1 \
        libgtk-3-0 libnss3 libu2f-udev libvulkan1 libxcomposite1 \
        libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xvfb fluxbox \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . .
COPY vendor/reg-factory /app/reg-factory
COPY docker/entrypoint.headed.sh /usr/local/bin/entrypoint.headed.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.headed.sh && chmod +x /usr/local/bin/entrypoint.headed.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.headed.sh"]
