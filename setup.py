#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='download_server',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=['tornado>=4.3'],
    tests_require=['coverage', 'selenium'],
    test_suite='tests',
)
