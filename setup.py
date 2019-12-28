#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rdm6300",
    version="0.1.1",
    author="The Mad Thinkerer Me",
    author_email="mad.tiknerer.me@gmail.com",
    description="RDM6300/EM4100 RFID reader library",
    long_description=long_description,
    install_requires=[
        "pyserial",
    ],
    tests_require=[
        "pyserial",
        "mock",
    ],
    long_description_content_type="text/markdown",
    url="https://github.com/mad-tinkerer/python-rdm6300",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
