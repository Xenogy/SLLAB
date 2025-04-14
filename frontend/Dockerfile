# ./Dockerfile

# ---- Base Node image ----
# Use an official Node.js Alpine image for a smaller footprint. Choose a specific LTS version.
FROM node:20-alpine AS base
# Set the working directory in the container
WORKDIR /usr/src/app


# ---- Dependencies Stage ----
# Install dependencies first to leverage Docker build cache
FROM base AS deps
# Copy package.json and lock file from the 'nextjs' subdirectory
COPY nextjs/package.json nextjs/package-lock.json* ./
# Use npm ci with legacy-peer-deps to handle React 19 compatibility issues
RUN npm ci --legacy-peer-deps


# ---- Build Stage ----
# Build the Next.js application
FROM base AS builder
# Copy dependencies from the 'deps' stage
COPY --from=deps /usr/src/app/node_modules ./node_modules
# Copy the rest of the application code from the 'app' subdirectory
COPY nextjs/ ./
# Set NODE_ENV to production for build optimizations
ENV NODE_ENV production
# Pass API URL from build arg
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
# Build the Next.js application
# This uses the 'output: "standalone"' feature defined in next.config.js
RUN npm run build --legacy-peer-deps


# ---- Production Stage ----
# Create the final, minimal image
FROM node:20-alpine AS runner
WORKDIR /usr/src/app

# Set NODE_ENV to production for runtime
ENV NODE_ENV production
# Optional: Expose the port Next.js will run on (default 3000)
ENV PORT 3000
# Pass API URL from build arg to runtime
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Create a non-root user and group for security
# Using standard names often found in node images
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy only the necessary artifacts from the builder stage
# Copy the standalone Next.js server output
COPY --from=builder /usr/src/app/.next/standalone ./
# Copy the static assets (needed by the server)
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/.next/static ./.next/static
# Copy the public assets (needed by the server)
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/public ./public

# Switch to the non-root user
USER nextjs

# Expose the port the app runs on
EXPOSE 3000

# The command to run the standalone Next.js server
CMD ["node", "server.js"]