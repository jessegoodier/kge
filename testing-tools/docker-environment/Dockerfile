# Stage 1: Build stage
FROM ubuntu:latest AS builder

# Create non-root user and set up sudo
RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    zlib1g-dev \
    libmpc-dev \
    libgmp-dev \
    sudo zsh wget vim curl git \
    && rm -rf /var/lib/apt/lists/*

# Create user and set up sudo without password
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu \
    && chmod 0440 /etc/sudoers.d/ubuntu

# Switch to non-root user
USER ubuntu
WORKDIR /home/ubuntu

# Install Homebrew as non-root user
RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    && echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc \
    && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" \
    && brew install gcc \
    && brew postinstall gcc \
    && brew cleanup

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && git clone https://github.com/djui/alias-tips.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/alias-tips \
    && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting \
    && git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions \
    && git clone https://github.com/superbrothers/zsh-kubectl-prompt.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-kubectl-prompt \
    && git clone https://github.com/zsh-users/zsh-completions ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-completions \
    && wget https://raw.githubusercontent.com/jessegoodier/jesse-zsh-profile/main/.zshrc -O $HOME/.zshrc \
    && wget https://raw.githubusercontent.com/jessegoodier/jesse-zsh-profile/main/.vimrc -O $HOME/.vimrc \
    && wget https://raw.githubusercontent.com/jessegoodier/jesse-zsh-profile/main/.prompt.zsh -O $HOME/.prompt.zsh \
    && mkdir -p ~/.kube-scripts \
    && wget https://raw.githubusercontent.com/jessegoodier/kgc/main/kgc.sh -O $HOME/.kube-scripts/kgc.sh \
    && wget https://raw.githubusercontent.com/jessegoodier/jesse-zsh-profile/main/.kube-scripts/aliases.sh -O $HOME/.kube-scripts/aliases.sh \
    && sed -i "s/alias ksd/#  alias ksd/" ~/.oh-my-zsh/plugins/kubectl/kubectl.plugin.zsh \
    && sudo chown -R ubuntu:ubuntu $HOME

# Stage 2: Python application stage
FROM builder AS python-app

# Copy necessary files from builder stage
COPY --from=builder --chown=ubuntu:ubuntu /home/linuxbrew/.linuxbrew /home/linuxbrew/.linuxbrew

WORKDIR /home/ubuntu/app

USER ubuntu
RUN export ZSH_HISTORY_PREPOP=': 1745435735:0;pipx install kge-kubectl-get-events\n: 1745766529:0;brew tap jessegoodier/kge\n: 1745766541:0;brew install -v kge\n: 1745767328:0;kge\n: 1745767979:0;brew list\n: 1745767989:0;kge\n: 1745767993:0;kgp\n: 1745768031:0;source <(kge --completion=zsh)' \
    && echo 'export PATH="/home/ubuntu/.local/bin:/home/linuxbrew/.linuxbrew/bin:${PATH}"' >> ~/.bashrc \
    && echo 'export PATH="/home/ubuntu/.local/bin:/home/linuxbrew/.linuxbrew/bin:${PATH}"' >> ~/.zshrc \
    && /home/linuxbrew/.linuxbrew/bin/brew install python@3.13 pipx \
    && echo "export KUBECONFIG=./.kubeconfig" >> ~/.zshrc \
    && echo "export KUBECONFIG=./.kubeconfig" >> ~/.bashrc \
    && echo "$ZSH_HISTORY_PREPOP" >/home/ubuntu/.zsh_history \
    && sudo chsh -s /bin/zsh ubuntu
