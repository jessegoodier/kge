from setuptools import setup, find_packages
import os

# Get the absolute path to the completion directory
completion_dir = os.path.join(os.path.dirname(__file__), 'kge', 'completion')
completion_files = [os.path.join('completion', f) for f in os.listdir(completion_dir) 
                   if os.path.isfile(os.path.join(completion_dir, f))]

setup(
    name="kge-kubectl-get-events",
    version="0.5.3",
    description="Kubernetes utility for viewing pod and failed replicaset events",
    author="Jesse Goodier",
    author_email="31039225+jessegoodier@users.noreply.github.com",
    packages=find_packages(include=['kge']),
    package_data={
        'kge': completion_files,
    },
    data_files=[
        ('share/zsh/site-functions', ['kge/completion/_kge']),
    ],
    install_requires=[
        'kubernetes',
        'colorama',
        'six',
    ],
    entry_points={
        'console_scripts': [
            'kge=kge.cli.main:main',
            'kge-install-completions=kge.completion.install:install_completions',
        ],
    },
    python_requires='>=3.11',
)