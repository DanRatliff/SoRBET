from setuptools import setup, find_packages

setup(
    name="sorbet",
    version="0.1.0",
    description="Sonic Radiation Belt Environment Toolkit",
    author="Daniel Ratliff",
    url="https://github.com/DanRatliff/SoRBET",
    packages=find_packages(),
    install_requires=[
        "strauss",
        "numpy",
        "matplotlib",
        "cdflib",
    ],
    python_requires=">=3.9",
)
