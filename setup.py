# setup.py
from setuptools import setup, find_packages

setup(
    name="sorbet",
    version="0.1.1",
    description="Sonic Radiation Belt Environment Toolkit",
    author="Daniel Ratliff",
    url="https://github.com/DanRatliff/SoRBET",
    packages=find_packages(),
    package_data={
        'sorbet': ['FReESR.json', 'Samples/**/*.wav', 'Samples/**/*.sf2'],
    },
    include_package_data=True,
    install_requires=[
        "strauss",
        "numpy",
        "matplotlib",
        "cdflib",
        "pydub",
    ],
    python_requires=">=3.9",
)