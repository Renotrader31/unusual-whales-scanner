"""
Setup script for UW Scanner
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="uw-scanner",
    version="1.0.0",
    author="Your Name",
    description="Ultimate stock and options scanner powered by Unusual Whales API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "aiohttp>=3.9.1",
        "requests>=2.31.0",
        "websockets>=12.0",
        "httpx>=0.25.2",
        "tenacity>=8.2.3",
        "aiolimiter>=1.1.0",
        "backoff>=2.2.1",
        "polars>=0.20.2",
        "pandas>=2.1.4",
        "numpy>=1.26.2",
        "scipy>=1.11.4",
        "pytz>=2023.3",
        "asyncpg>=0.29.0",
        "sqlalchemy>=2.0.23",
        "alembic>=1.13.1",
        "redis>=5.0.1",
        "psycopg2-binary>=2.9.9",
        "fastapi>=0.108.0",
        "uvicorn>=0.25.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "streamlit>=1.29.0",
        "plotly>=5.18.0",
        "celery>=5.3.4",
        "apscheduler>=3.10.4",
        "discord.py>=2.3.2",
        "python-telegram-bot>=20.7",
        "python-dotenv>=1.0.0",
        "scikit-learn>=1.3.2",
        "xgboost>=2.0.3",
        "loguru>=0.7.2",
        "prometheus-client>=0.19.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "pyyaml>=6.0.1",
        "python-dateutil>=2.8.2",
        "rich>=13.7.0",
        "tqdm>=4.66.1",
    ],
    entry_points={
        "console_scripts": [
            "uw-scanner=main:main",
        ],
    },
)
