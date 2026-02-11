# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Accept build arguments
ARG VITE_NODE_API_URL
ARG VITE_FASTAPI_URL

# Set them as environment variables for the build process
ENV VITE_NODE_API_URL=$VITE_NODE_API_URL
ENV VITE_FASTAPI_URL=$VITE_FASTAPI_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
