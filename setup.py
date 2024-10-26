from setuptools import setup, find_packages

setup(
    name="economy_simulation",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'mesa>=1.0.0',
        'matplotlib>=3.5.0',
        'numpy>=1.21.0',
        'pandas>=1.3.0',
        'ipython>=7.0.0',
    ],
)