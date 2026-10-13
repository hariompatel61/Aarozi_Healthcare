FROM python:3.11-slim

# Install system dependencies (build essentials, postgres dev libs, curl for node)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Node 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/Aarozi_Healthcare

# Install dev Python tools
RUN pip install --no-cache-dir \
    pytest \
    ruff \
    mypy \
    alembic \
    uvicorn

CMD ["sleep", "infinity"]
