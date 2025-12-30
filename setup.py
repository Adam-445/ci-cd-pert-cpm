from setuptools import setup, find_packages

setup(
    name="pert-cpm",
    version="1.0.1",
    # package configuration
    packages=find_packages(exclude=["tests", "tests.*", "notebooks", "scripts"]),
    # dependencies
    install_requires=[
        "matplotlib>=3.10.0",
        "networkx>=3.6.0",
        "numpy>=2.4.0",
        "pandas>=2.3.0",
    ],
    # development dependencies
    extras_require={
        "dev": [
            "pytest>=9.0.0",
            "pytest-cov>=7.0.0",
            "jupyter>=1.0.0",
        ]
    },
)
