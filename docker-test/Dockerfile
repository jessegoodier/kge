# Stage 1: Build stage
FROM ubuntu:latest AS builder

# Install Python 3.11 and pip
RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    zlib1g-dev \
    libmpc-dev \
    libgmp-dev \
    && apt-get update \
    && apt-get install -y vim curl git \
    && rm -rf /var/lib/apt/lists/* \
    && /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    && echo >> /root/.bashrc \
    && echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /root/.bashrc \
    && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" \
    && brew install gcc \
    && brew postinstall gcc

# Stage 2: Python application stage
FROM builder AS python-app

# Copy necessary files from builder stage
COPY --from=builder /home/linuxbrew/.linuxbrew /home/linuxbrew/.linuxbrew

# Install Python 3.13
RUN /home/linuxbrew/.linuxbrew/bin/brew install python@3.13

# Set up Python environment
RUN home/linuxbrew/.linuxbrew/bin/pip3 install --break-system-packages --root-user-action=ignore --upgrade pip
RUN /home/linuxbrew/.linuxbrew/bin/python3 -m venv venv
# RUN source venv/bin/activate
# RUN pip install poetry
# RUN poetry check
# RUN poetry run pytest --cov=./ --cov-report=xml
