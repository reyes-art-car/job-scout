# syntax=docker/dockerfile:1
# Frontend Angular servido por nginx sin privilegios. Construir desde la raíz del repositorio.

FROM node:22-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --ignore-scripts
COPY frontend ./frontend
COPY data/demo ./data/demo
RUN cd frontend && npx ng build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY infra/nginx/job-hunter.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/frontend/dist/job-hunter/browser /usr/share/nginx/html
EXPOSE 8080
