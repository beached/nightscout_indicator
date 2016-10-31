#!/usr/bin/env python3

from setuptools import setup

setup( 
    name='nightscout_indicator',
    version='0.1',
    description='Display pertinent Nightscout data',
    url='https://github.com/beached/nightscout_indicator',
    author='Darrell Wright',
    author_email='Darrell.Wright@gmail.com',
    license='MIT',
    packages=['nightscout_indicator'],
    install_requires=[
        'requests',
        'gi',
        'pysocks'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    zip_safe=False
)



