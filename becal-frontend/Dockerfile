# Construye con el repositorio completo como contexto (docker compose ya lo hace):
#   docker build -f becal-frontend/Dockerfile .
FROM node:22-alpine AS build
WORKDIR /app
# leaflet y tailwind viven en el package.json de la raíz
COPY package.json package-lock.json ./
RUN npm ci
WORKDIR /app/becal-frontend
COPY becal-frontend/package.json becal-frontend/package-lock.json ./
RUN npm ci
COPY becal-frontend/ ./
RUN npx ng build --configuration production

FROM nginx:1.27-alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/becal-frontend/dist/becal-frontend/browser /usr/share/nginx/html
EXPOSE 80
