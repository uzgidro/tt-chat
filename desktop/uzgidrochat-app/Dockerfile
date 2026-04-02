# Шаг 1: Сборка Angular
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration production

# Шаг 2: Nginx раздаёт собранные файлы
FROM nginx:alpine

# Удаляем дефолтный конфиг nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг
COPY ../../nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранный Angular (dist/uzgidrochat-app/browser/)
COPY --from=builder /app/dist/uzgidrochat-app/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
