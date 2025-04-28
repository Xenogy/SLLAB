# ./Dockerfile.optimized

# ---- Base Node image ----
FROM node:20-alpine AS base
WORKDIR /usr/src/app

# ---- Dependencies Stage ----
FROM base AS deps
# Copy only package files to leverage layer caching
COPY nextjs/package.json nextjs/package-lock.json* ./
# Use cache mount for npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps --prefer-offline

# ---- Build Stage ----
FROM base AS builder
# Copy dependencies from the 'deps' stage
COPY --from=deps /usr/src/app/node_modules ./node_modules
# Copy only necessary files for the build
COPY nextjs/public ./public
COPY nextjs/app ./app
COPY nextjs/components ./components
COPY nextjs/lib ./lib
COPY nextjs/hooks ./hooks
COPY nextjs/styles ./styles
COPY nextjs/*.js ./
COPY nextjs/*.ts ./
COPY nextjs/*.tsx ./
COPY nextjs/*.json ./
COPY nextjs/*.mjs ./

# Set NODE_ENV to production for build optimizations
ENV NODE_ENV production
# Pass API URL from build arg
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the Next.js application with cache mount for .next/cache
RUN --mount=type=cache,target=/usr/src/app/.next/cache \
    npm run build --legacy-peer-deps

# ---- Production Stage ----
FROM node:20-alpine AS runner
WORKDIR /usr/src/app

# Set NODE_ENV to production for runtime
ENV NODE_ENV production
ENV PORT 3000
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Create a non-root user and group for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only the necessary artifacts from the builder stage
COPY --from=builder /usr/src/app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /usr/src/app/public ./public

# Switch to the non-root user
USER nextjs

# Expose the port the app runs on
EXPOSE 3000

# The command to run the standalone Next.js server
CMD ["node", "server.js"]
