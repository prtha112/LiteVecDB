from setuptools import setup, find_packages

setup(
    name="litevecdb",
    version="0.1.0",
    description="Lightweight sharded vector DB with optional S3 support",
    author="prtha112",
    author_email="thahi5_vi@hotmail.com",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "zstandard",
    ],
    python_requires=">=3.12",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ]
)