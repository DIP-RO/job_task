FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files first for layer caching
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Run the application
CMD ["npm", "run", "dev"]