#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="margin_official_strategies",
    version="0.0.5",
    author="Margin UG",
    author_email="contact@margin.io",
    description="Official strategies by margin for the Margin Strategy Editor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarginOpenSource/official-strategies",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["margin-strategy-sdk"],
    python_requires='>=3.6',
)
