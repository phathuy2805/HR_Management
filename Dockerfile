# Sử dụng Node.js 20 Alpine nhẹ và bảo mật
FROM node:20-alpine AS builder

WORKDIR /app

# Cài đặt OpenSSL cần thiết cho Prisma Client
RUN apk add --no-cache openssl

# Copy file định nghĩa dependencies
COPY package*.json ./
COPY prisma ./prisma/

# Cài đặt toàn bộ dependencies và sinh mã Prisma Client
RUN npm ci
RUN npx prisma generate

# Copy toàn bộ mã nguồn và build ứng dụng NestJS
COPY . .
RUN npm run build

# ====================================================================
# Production Stage
# ====================================================================
FROM node:20-alpine AS runner

WORKDIR /app

RUN apk add --no-cache openssl

ENV NODE_ENV=production

# Copy các dependencies và sản phẩm build từ builder stage
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma

EXPOSE 3000

CMD ["node", "dist/main.js"]
