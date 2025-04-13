from setuptools import setup, find_packages

setup(
    name="kge-kubectl-get-events",
    version="0.5.1",
    description="Kubernetes utility for viewing pod and failed replicaset events",
    author="Jesse Goodier",
    author_email="31039225+jessegoodier@users.noreply.github.com",
    packages=find_packages(include=['kge']),
    install_requires=[
        'kubernetes',
        'colorama',
        'six',
    ],
    entry_points={
        'console_scripts': [
            'kge=kge.cli.main:main',
        ],
    },
    python_requires='>=3.11',
)