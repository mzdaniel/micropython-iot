from setuptools.config import read_configuration
from distutils.core import setup

conf_dict = read_configuration('setup.cfg')
setup()
