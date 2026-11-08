# Diagnostic tooling only; inherits the exact scientific wheel and libraries.
# Build with: docker build -f docker/diagnostics.Dockerfile -t trajectory-pipeline:memcheck docker
ARG TRAJECTORY_BASE=trajectory-pipeline:kiam-6.1.6-py312
FROM ${TRAJECTORY_BASE}
RUN apt-get update \
    && apt-get install -y --no-install-recommends valgrind \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["valgrind"]
