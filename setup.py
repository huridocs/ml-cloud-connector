from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

PROJECT_NAME = "ml-cloud-connector"

setup(
    name=PROJECT_NAME,
    packages=["ml_cloud_connector"],
    package_dir={"": "src"},
    version="0.6",
    url="https://github.com/gabriel-piles/ml-cloud-connector",
    author="HURIDOCS",
    description="This tool is a ml cloud connector",
    install_requires=requirements,
    setup_requieres=requirements,
)
