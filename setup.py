from setuptools import setup
import ajson_rpc2


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
    keywords='howdoi help console command line answer',
    author='WindSoilder',
    author_email='WindSoilder@outlook.com',
    maintainer='WindSoilder',
    maintainer_email='WindSoilder@outlook.com',
    url='https://github.com/WindSoilder/ajson-rpc2',
    license='MIT',
    packages=['ajson_rpc2']
)
