from setuptools import setup, find_packages

setup(
    name         = 'tipprapi',
    version      = '1.0',
    packages     = find_packages(),
    install_requires=[
        'setuptools',
        'simplejson==2.2.1'
      ]
)
