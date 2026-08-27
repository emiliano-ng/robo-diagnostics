# --- deps: instala dependencias por separado para aprovechar cache de Docker ---
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- builder: compila con las variables NEXT_PUBLIC_* ya "horneadas" ---
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* se inyecta en el bundle en build time, no en runtime —
# por eso va como build ARG, no como variable de entorno del contenedor final.
ARG NEXT_PUBLIC_API_BASE_URL=http://backend:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN npm run build

# --- runner: imagen final, solo lo que standalone necesita para correr ---
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
