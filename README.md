# Repository Scraper

## Description

This module fetches data from a specified repository URL using aiohttp and
Beautiful Soup, saves any files found to the local file system and calculates
the SHA-256 hash for all files downloaded to the local file system.

Scraper has 100% test coverage


## Getting started

### Installing

Clone repository and spawn venv and install dependencies with Poetry or like this:

```
python3 -m venv venv
```

```
pip install -r requirements.txt
```

### Usage

The script can be executed from the command line as follows:

```
python main.py
```

It will scrape repository by this URL:

https://gitea.radium.group/radium/project-configuration 


And generate 'repository_sha256.csv' file.
