#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="em4100-mad-tinkerer",
    version="0.1.0",
    author="The Mad Thinkerer Me",
    author_email="mad.tiknerer.me@gmail.com",
    description="EM4100 rfid reader",
    long_description=long_description,
    install_requires=[
        "pyserial",
    ],
    tests_require=[
        "pyserial",
        "mock",
    ],
    long_description_content_type="text/markdown",
    url="https://github.com/mad-tinkerer/python-em4100",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
