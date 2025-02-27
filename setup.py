from setuptools import setup, find_packages

setup(
    name="ye_meme_trader",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-telegram-bot>=21.0",
        "redis>=4.0.0",
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=0.19.0",
        "solana>=0.35.0",
        "solders>=0.21.0",
        "anchorpy>=0.20.1",
        "jupiter-python-sdk>=0.0.2.0",
        "bitstring>=4.3.0",
        "asyncio>=3.4.3",
        "websockets>=10.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "sentry-sdk>=1.0.0",
        "beautifulsoup4>=4.12.0",
    ],
    python_requires=">=3.9",
)
