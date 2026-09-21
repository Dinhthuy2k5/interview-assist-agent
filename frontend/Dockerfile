FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host để Vite bind 0.0.0.0 thay vì 127.0.0.1 (loopback),
# bắt buộc để Traefik trong Docker network reach được container này.
CMD ["npm", "run", "dev", "--", "--host"]