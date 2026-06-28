FROM node:24-bookworm

WORKDIR /app/src/finmind_ui

COPY src/finmind_ui/package.json src/finmind_ui/package-lock.json ./
RUN npm ci

COPY src/finmind_ui ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
