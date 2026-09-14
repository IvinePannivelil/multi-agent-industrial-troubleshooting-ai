FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
CMD ["sh", "-c", "npm install && npm run dev --workspace=apps/goose-elevate"]
