# kge-kubectl-get-events

A kubernetes utility for viewing pod events in a user-friendly way.
There are many problems that are most easily fixed by understand the recent events for the pods. 
The best alternative to this tool is:

```sh
alias kge="kubectl get events --sort-by=lastTimestamp --field-selector type!=Normal"
```

## Table of Contents

- [kge-kubectl-get-events](#kge-kubectl-get-events)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [View Events for All Pods](#view-events-for-all-pods)
    - [View Events for a Specific Pod](#view-events-for-a-specific-pod)
    - [View Non-Normal Events](#view-non-normal-events)
    - [Specify Namespace](#specify-namespace)
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

### View Non-Normal Events

View only non-normal events (warnings and errors) for all pods:

```bash
kge --exceptions-only
# or
kge -e
```

In interactive mode, you can select "All pods with non-normal events" from the menu.

### Specify Namespace

View events from a specific namespace:

```bash
kge -n mynamespace
# or
kge --namespace mynamespace
```

You can combine this with other options:

```bash
# View all events in a specific namespace
kge -A -n mynamespace

# View non-normal events in a specific namespace
kge -e -n mynamespace

# View events for a specific pod in a specific namespace
kge -n mynamespace my-pod
```

### Interactive Mode

Run the tool without arguments to enter interactive mode:

```bash
kge
```

This will display a menu of all pods in the current namespace, allowing you to select which pod's events to view. The menu includes an option to view all non-normal events.

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
| `-n, --namespace` | Specify the namespace to use |
| `-e, --exceptions-only` | Show only non-normal events (warnings and errors) |
| `--complete` | List pods for shell completion (internal use) |
| `--completion=zsh` | Generate zsh completion script |

## Features

- View events for all pods in a namespace
- View events for a specific pod
- View only non-normal events (warnings and errors)
- Specify custom namespace
- Interactive pod selection
- Shell completion support
- Automatic namespace detection
- Caching for better performance

## Requirements

- Python 3.6 or higher
- Valid Kubeconfig in the environment
