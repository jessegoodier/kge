FROM ubuntu:latest

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
