# kge-kubectl-get-events

A kubectl plugin for viewing Kubernetes events in a user-friendly way.

## Table of Contents

- [kge-kubectl-get-events](#kge-kubectl-get-events)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [View Events for All Pods](#view-events-for-all-pods)
    - [View Events for a Specific Pod](#view-events-for-a-specific-pod)
    - [Interactive Mode](#interactive-mode)
    - [Shell Completion](#shell-completion)
      - [For zsh](#for-zsh)
  - [Command-line Options](#command-line-options)
  - [Features](#features)
  - [Requirements](#requirements)

## Installation

```bash
pipx install kge-kubectl-get-events
```

## Usage

### View Events for All Pods

View events for all pods in the current namespace:

```bash
kge -A
# or
kge --all
```

### View Events for a Specific Pod

View events for a specific pod:

```bash
kge <pod-name>
```

### Interactive Mode

Run the tool without arguments to enter interactive mode:

```bash
kge
```

This will display a menu of all pods in the current namespace, allowing you to select which pod's events to view.

### Shell Completion

The tool supports shell completion for pod names. To enable it:

#### For zsh

Add the following to your shell configuration:

```bash
source <(kge --completion=zsh)
```

Alternatively, add the completion script directly to your zsh configuration:

```bash
compdef _kge kge
_kge() {
    local -a pods
    pods=($(kge --complete))
    _describe 'pods' pods
}
```

## Command-line Options

| Option | Description |
|--------|-------------|
| `-A, --all` | Get events for all pods in the current namespace |
| `--complete` | List pods for shell completion (internal use) |
| `--completion=zsh` | Generate zsh completion script |

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