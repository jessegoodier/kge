# kge - Kubernetes Events Viewer

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/kge-kubectl-get-events)](https://pypi.org/project/kge-kubectl-get-events/)

A simple yet powerful CLI tool for viewing and monitoring Kubernetes events with a focus on readability and ease of use. `kge` provides an intuitive interface to quickly diagnose issues.

## Table of Contents

- [kge - Kubernetes Events Viewer](#kge---kubernetes-events-viewer)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Basic Usage](#basic-usage)
    - [Viewing Events for Any Resource Type](#viewing-events-for-any-resource-type)
    - [Interactive Mode](#interactive-mode)
    - [Shell Completion](#shell-completion)
  - [Examples](#examples)
  - [Known Issues](#known-issues)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- 🔍 View events for specific pods
- 📊 View all events in a namespace
- ⚠️ Filter to show only non-normal events
- 🖱️ Interactive pod selection
- 🎨 Color-coded output
- ⌨️ Shell completion support (zsh)
- 🔄 View events for any Kubernetes resource type (Pods, Deployments, etc.)

## Installation

```bash
# Install using pipx (recommended)
pipx install kge
```

```bash
# Or install using pip
pip install kge
```

## Usage

### Basic Usage

View events for a specific pod:

```bash
kge <pod-name>
```

View all events in the current namespace:

```bash
kge -a
```

View only non-normal events:

```bash
kge -e
```

Combine flags to view all non-normal events in the current namespace:

```bash
kge -ea
```

View events in a specific namespace:

```bash
kge -n <namespace>
```

### Viewing Events for Any Resource Type

View events for a specific resource type:

```bash
kge -k <kind> <resource-name>
```

Examples:

```bash
# View events for a Deployment
kge -k Deployment my-deployment

# View events for a Lease in kube-system namespace
kge -n kube-system -k Lease kube-controller-manager

# View events for a Service
kge -k Service my-service
```

### Interactive Mode

Run without arguments for interactive pod selection:

```bash
kge
```

### Shell Completion

Enable zsh completion:

```bash
source <(kge --completion=zsh)
```

Completion features:

- Tab completion for namespaces after `-n`
- Tab completion for pods after `-n <namespace>`
- Tab completion for kinds after `-k`
- Tab completion for resources of a specific kind after `-k <kind>`

## Examples

View non-normal events for all pods in a namespace:

```bash
kge -ea
```

View events for a specific pod in a specific namespace:

```bash
kge -n my-namespace my-pod
```

View events for a Deployment:

```bash
kge -k Deployment my-deployment
```

## Known Issues

- Not all arguments work together. For example, `kge -e -k Deployment` will not work. For complex queries, use `kge -a` to see all events and filter with `grep` or another tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
