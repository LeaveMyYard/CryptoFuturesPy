from setuptools import setup, find_packages

setup(
    name="crypto_futures_py",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    # metadata to display on PyPI
    author="LeaveMyYard",
    author_email="zhukovpavel2001@gmail.com",
    description="The Python library of different implementations for exchange interface of cryptocurrency futures trading. Includes Bitmex and Binance Futures.",
    url="https://github.com/LeaveMyYard/CryptoFuturesPy",  # project home page, if any
    project_urls={"Source Code": "https://github.com/LeaveMyYard/CryptoFuturesPy",},
    classifiers=["License :: OSI Approved :: Python Software Foundation License"],
)
