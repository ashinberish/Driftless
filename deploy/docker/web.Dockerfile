# syntax=docker/dockerfile:1.7
FROM node:26-alpine AS build
RUN corepack enable
WORKDIR /src
COPY frontend/ ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile && pnpm build

FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/apps/web/dist /usr/share/nginx/html
EXPOSE 8080
