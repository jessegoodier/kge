from setuptools import setup, find_packages

setup(
    name="kge",
    version="0.4.0",
    description="A tool to get Kubernetes events",
    author="Jesse",
    packages=find_packages(include=['kge']),
    install_requires=[
        'kubernetes',
        'colorama',
    ],
    entry_points={
        'console_scripts': [
            'kge=kge.cli.main:main',
        ],
    },
    python_requires='>=3.6',
) 