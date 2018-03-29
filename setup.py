from setuptools import setup
import os
import ajson_rpc2


def read(*names):
    values = dict()
    extensions = ['.txt', '.md']
    for name in names:
        value = ''
        for extension in extensions:
            filename = name + extension
            if os.path.isfile(filename):
                value = open(name + extension).read()
                break
        values[name] = value
    return values


long_description = '''
%(README)s
''' % read('README')


setup(
    name='ajson_rpc2',
    version=ajson_rpc2.__version__,
    description='json rpc 2.0 implementations based on python3 asyncio module',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Topic :: Documentation",
    ],
    keywords=["rpc", "json", "server"],
    author='WindSoilder',
    author_email='WindSoilder@outlook.com',
    maintainer='WindSoilder',
    maintainer_email='WindSoilder@outlook.com',
    url='https://github.com/WindSoilder/ajson-rpc2',
    license='MIT',
    packages=['ajson_rpc2', 'ajson_rpc2.models']
)
