"""
Setup script for the Windows VM Agent.

This script installs the agent as a Python package and creates necessary directories.
"""
from setuptools import setup, find_packages
import os

# Read the version from __init__.py
with open('__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip("'").strip('"')
            break
    else:
        version = '0.0.1'

# Read the long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='windows_vm_agent',
    version=version,
    description='Dynamic Windows VM Agent for monitoring and executing actions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/windows_vm_agent',
    packages=['agent', 'api', 'config', 'monitors', 'scripts', 'utils'],
    include_package_data=True,
    install_requires=[
        'pyyaml>=6.0',
        'requests>=2.28.0',
    ],
    entry_points={
        'console_scripts': [
            'windows-vm-agent=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.7',
)
