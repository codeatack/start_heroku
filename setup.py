from setuptools import setup, find_packages

setup(
    name='hikka',
    version='0.1.0',
    packages=find_packages(),
    description='A Python module to run Heroku',
    author='codeatack',
    author_email='codeatack1@gmail.com',
    install_requires=[],
    entry_points={
        'console_scripts': [
            'hikka=hikka.main:run_hikka',
        ],
    },
)
