FROM node:24-bookworm

WORKDIR /app/src/ui

COPY src/ui/package.json src/ui/package-lock.json ./
RUN npm ci

COPY src/ui ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
