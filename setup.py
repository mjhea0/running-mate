import setuptools
from pathlib import Path

BASE = Path(__file__).parent
long_description = (BASE / "README.md").read_text()


setuptools.setup(
    name="running-mate",
    version="0.0.5",
    author="Michael Herman",
    author_email="michael@mherman.org",
    description="Lightweight MLOps framework.",
    url="https://github.com/mjhea0/running-mate",
    packages=setuptools.find_packages(),
    install_requires=[
        "dacite==1.6.0",
        "numpy==1.21.3",
        "pandas==1.3.4",
        "peewee==3.14.8",
        "requests==2.26.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown"
)
