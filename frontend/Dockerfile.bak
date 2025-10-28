FROM node:20-alpine
WORKDIR /app

# Copy only manifests first (better cache). Include lockfile if present.
COPY package.json package-lock.json* ./

# Install deps (use npm ci if lockfile exists)
RUN [ -f package-lock.json ] && npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# Copy the rest of the app
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
