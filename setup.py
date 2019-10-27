from setuptools import setup

setup(
    name='RokuPi',
    version='1.0',
    py_modules=['rokuPi'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        rokuPi=rokuPi:deploy
    ''',
)