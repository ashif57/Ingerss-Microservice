# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# No build step necessary for simple Node.js express app unless using typescript/babel

# Production stage
FROM gcr.io/distroless/nodejs18-debian12

WORKDIR /app

COPY --from=builder /app/index.js ./index.js
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3001

CMD ["index.js"]
