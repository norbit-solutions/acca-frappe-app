# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in acca_lms/__init__.py
from acca_lms import __version__ as version

setup(
	name="acca_lms",
	version=version,
	description="Secure video streaming Learning Management System with Mux integration",
	author="NorBit Solutions",
	author_email="info@norbitsolutions.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
