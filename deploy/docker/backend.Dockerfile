# syntax=docker/dockerfile:1.7
# One image recipe for every backend app: docker build --build-arg APP=api|worker
ARG PYTHON_VERSION=3.14

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:${PYTHON_VERSION}-slim AS build
ARG APP
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /src
COPY backend/ ./
# Install only the selected app and the libraries it depends on.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package "driftless-${APP}" --no-editable

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG APP
ENV PATH="/src/.venv/bin:${PATH}" PYTHONUNBUFFERED=1 APP=${APP}
RUN useradd --system --uid 10001 driftless
COPY --from=build /src/.venv /src/.venv
USER 10001
EXPOSE 8000
ENTRYPOINT ["sh", "-c", "exec driftless-${APP}"]
