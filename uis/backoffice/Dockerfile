FROM node:24-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.18.3 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY next.config.ts tsconfig.json next-env.d.ts ./
COPY src ./src
COPY contracts ./contracts
COPY scripts ./scripts
COPY operational-incidents/telemetry ./operational-incidents/telemetry
COPY operational-incidents/favicon.svg ./operational-incidents/favicon.svg
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build
FROM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3100
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3100
CMD ["node","server.js"]
