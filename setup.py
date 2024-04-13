from setuptools import setup, find_packages


setup(
    name="ephemeral",
    version="0.0.1",
    author="Mathias Darr",
    author_email="mddarr@gmail.com",
    packages=find_packages(),
    entry_points={
        "ephemeral.init": [],
        "console_scripts": ["ephemeral = ephemeral.manage:cli"],
    }
)