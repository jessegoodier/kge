# kge-kubectl-get-events - Kubernetes Events Viewer

A kubectl plugin for viewing Kubernetes events in a user-friendly way.

## Installation

```bash
pip install kge-kubectl-get-events
```

## Usage

### View events for all pods in current namespace
```bash
kge -A
# or
kge --all
```

### View events for a specific pod
```bash
kge <pod-name>
```

### Interactive mode
```bash
kge
```

This will show a menu of all pods in the current namespace, allowing you to select which pod's events to view.

### Shell completion
The tool supports shell completion for pod names. To use it, add the following to your shell configuration:

For zsh:
```bash
source <(kge --completion=zsh)
```

Alternatively, you can add the completion script directly to your zsh configuration:
```bash
compdef _kge kge
_kge() {
    local -a pods
    pods=($(kge --complete))
    _describe 'pods' pods
}
```

### Command-line Options
- `-A, --all`: Get events for all pods in the current namespace
- `--complete`: List pods for shell completion (internal use)
- `--completion=zsh`: Generate zsh completion script

## Features

- View events for all pods in a namespace
- View events for a specific pod
- Interactive pod selection
- Shell completion support
- Automatic namespace detection
- Caching for better performance

## Requirements

- Python 3.6 or higher
- Kubernetes Python client
- kubectl configured with access to a Kubernetes cluster 