import setuptools
import os

setuptools.setup(
    name="mate",
    version="0.0.0",
    author="Michael Herman",
    author_email="michael@testdriven.io",
    description="Lightweight model monitoring framework.",
    url="https://github.com/testdrivenio/mate",
    packages=setuptools.find_packages(),
    install_requires=[
        "dacite==1.6.0",
        "numpy==1.21.3",
        "pandas==1.3.4",
        "requests==2.26.0",
    ],
)
