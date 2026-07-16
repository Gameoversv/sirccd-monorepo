FROM node:20-alpine

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm ci

# Copiar código
COPY . .

# NEXT_PUBLIC_* se hornea en el bundle durante el build, no en runtime:
# tiene que estar presente como ARG antes de `npm run build`.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build de producción
RUN npm run build

ENV PORT=3000
EXPOSE 3000

ENV NODE_ENV=production

CMD npm start -- --port ${PORT}
