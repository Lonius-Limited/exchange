from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in exchange/__init__.py
from exchange import __version__ as version

setup(
	name="exchange",
	version=version,
	description="Healthcare Information Exchange app",
	author="Lonius Limited",
	author_email="info@lonius.co.ke",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
