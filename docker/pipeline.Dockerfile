FROM python:3.12-slim-trixie@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONFAULTHANDLER=1 \
    MPLCONFIGDIR=/tmp/matplotlib OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    TRAJECTORY_RUNTIME=docker-linux

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates libgfortran5 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory /workspace

COPY third_party/kiam_astro/kiam_astro-6.1.6-cp312-cp312-manylinux_2_38_x86_64.whl /opt/wheels/
RUN echo "fe15a29c1a55cb4e8aa0867c21384f7bf6947018fa6077660b2f6cbe0294716b  /opt/wheels/kiam_astro-6.1.6-cp312-cp312-manylinux_2_38_x86_64.whl" | sha256sum --check
COPY docker/requirements.lock.txt /opt/requirements.lock.txt
RUN python -m pip install --no-cache-dir -r /opt/requirements.lock.txt && python -m pip check

WORKDIR /workspace
ENTRYPOINT ["python", "-m", "trajectory_pipeline"]
