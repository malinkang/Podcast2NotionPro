from setuptools import setup, find_packages

setup(
    name="podcast2notion",
    version="0.0.6",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pendulum",
        "retrying",
        "notion-client",
        "github-heatmap",
        "python-dotenv",
        "emoji",
    ],
    entry_points={
        "console_scripts": [
            "podcast = podcast2notion.podcast:main",
            "speech_text = podcast2notion.speech_text:main",
            "update_heatmap = podcast2notion.update_heatmap:main",
        ],
    },
    author="malinkang",
    author_email="linkang.ma@gmail.com",
    description="自动将习惯同步到Notion",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/malinkang/podcast2notionpro",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
