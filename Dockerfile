FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt gunicorn
COPY backend/ /app/backend/
COPY shared/ /app/shared/
COPY --from=frontend-build /build/frontend/dist/ /app/frontend/dist/
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
CMD ["sh", "-c", "gunicorn --chdir backend --bind 0.0.0.0:${PORT} --workers 1 --threads 4 wsgi:app"]
