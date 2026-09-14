FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
# For a raw dev environment starting from compose:
CMD ["sh", "-c", "npm install && npm run dev --workspace=apps/goose-mart"]
