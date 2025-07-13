from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gw2_teambuilder",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Guild Wars 2 Team Builder - Optimise your WvW team compositions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gw2-teambuilder",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Gamers",
        "Topic :: Games/Entertainment",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.29.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "deap>=1.3.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gw2-teambuilder=app.cli:main",
        ],
    },
)
