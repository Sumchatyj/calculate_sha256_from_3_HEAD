"""
This module fetches data from a specified repository URL using aiohttp and
Beautiful Soup, saves any files found to the local file system and calculates
the SHA-256 hash for all files downloaded to the local file system.

Functions:

save_file(session, semaphore, url, path): Downloads a file from the given URL
    and saves it to the specified path.
fetch_data(session, semaphore, local_path, url, tasks): Recursively fetches
    data from the given repository URL and
saves any files found to the specified directory.
calculate_sha256(file_path): Calculates the SHA-256 hash for
    the specified file.
calculate_sha256_for_directory(directory): Calculates the SHA-256 hash for
    all files in the specified directory
and writes the results to a CSV file.
main(): Starts the script.

Constants:

BASE_URL: The base URL for the repository.
PROJECT_URL: The URL for the repository.
PATTERN_TO_FIND: The pattern to find in URLs to replace with PATTERN_TO_SUB.
PATTERN_TO_SUB: The pattern to substitute in URLs.
CLASSES: A tuple containing the CSS classes to search for on the page.
PATH_TO_RESULT: The path to result of calculation.
SEMAPHORE_LIMIT: The maximum number of concurrent downloads.
"""

import asyncio
import csv
import hashlib
import os
import re
import logging

from aiohttp import ClientSession, client_exceptions
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


PATTERN_TO_FIND = '/src/branch'

PATTERN_TO_SUB = '/raw/branch'

CLASSES = ('octicon-file-directory-fill', 'octicon-file')

PATH_TO_RESULT = 'repository_sha256'

SEMAPHORE_LIMIT = 3


async def save_file(
    session: ClientSession, semaphore: asyncio.Semaphore, base_url: str, url: str, path: str,
) -> None:
    """
    Download a file from the given URL and saves it to the specified path.

    Args:
        session (ClientSession): An instance of the aiohttp ClientSession.
        semaphore (asyncio.Semaphore): An asyncio semaphore that limits
            the number of concurrent downloads.
        base_url (str): The URL of repository.
        url (str): The URL to download the file from.
        path (str): The directory to save the downloaded file to.
    """
    filename = url.split('/')[-1]
    async with semaphore:
        try:
            response = await session.get(base_url + url)
        except client_exceptions.ClientConnectorError:
            logger.error(
                f'An error occurred while downloading the file: {url}'
            )
            return None
        with open(f'{path}/{filename}', 'wb') as document:
            while True:
                data_part = await response.content.read(1024)
                if not data_part:
                    break
                document.write(data_part)


async def fetch_data(
    session: ClientSession,
    semaphore: asyncio.Semaphore,
    base_url: str,
    local_path: str,
    url: str,
) -> None:
    """
    Recursively fetches data from the given repository URL and saves any files
    found to the specified directory.

    Args:
        session (ClientSession): An instance of the aiohttp ClientSession.
        semaphore (asyncio.Semaphore): An asyncio semaphore that limits
            the number of concurrent downloads.
        base_url (str): The URL of repository.
        local_path (str): The directory to save the downloaded files to.
        url (str): The URL to fetch data from.
        tasks (list): The list of asyncio tasks
    """
    async with semaphore:
        try:
            response = await session.get(base_url + url)
        except client_exceptions.ClientConnectorError:
            logger.error(
                f'An error occurred while parsing the url: {url}'
            )
            return None
        soup = BeautifulSoup(await response.text(), 'lxml')
        objects_in_repo = soup.tbody.find_all(class_=CLASSES)
        for element in objects_in_repo:
            if element.get('class')[1] == CLASSES[1]:
                url_to_download = re.sub(
                    PATTERN_TO_FIND,
                    PATTERN_TO_SUB,
                    element.find_next_sibling().get('href')
                )
                await save_file(
                            session,
                            semaphore,
                            base_url,
                            url_to_download,
                            local_path,
                        )
            else:
                url_to_directory = element.find_next_sibling().get('href')
                new_path = os.path.join(
                    local_path, url_to_directory.split('/')[-1]
                )
                os.makedirs(new_path, exist_ok=True)
                await fetch_data(
                            session,
                            semaphore,
                            base_url,
                            new_path,
                            url_to_directory,
                        )


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash for the specified file.

    Args:
        file_path (str): The path to the file to calculate the hash for.

    Returns:
        str: The calculated SHA-256 hash as a hexadecimal string.
    """
    with open(file_path, 'rb') as file_reader:
        data_to_hash = file_reader.read()
    return hashlib.sha256(data_to_hash).hexdigest()


def calculate_sha256_for_directory(
    directory: str,
    path_to_result: str
) -> None:
    """
    Calculate the SHA-256 hash for all files in the specified directory
    and write the results to a CSV file.

    Args:
        directory (str): The directory to calculate SHA-256 hashes for.
        path_to_result (str): The path to result of calculation.
    """
    with open(path_to_result, 'w', newline='') as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=('file_path', 'sha256_hash')
        )
        writer.writeheader()
        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                sha256_hash = calculate_sha256(file_path)
                writer.writerow(
                    {'file_path': file_path, 'sha256_hash': sha256_hash}
                )



async def main(base_url: str, project_url: str, path_prefix: str = '') -> None:
    """
    Start the script.

    Fetches data from a specified URL and calculates the SHA-256 hash
    for all files downloaded to the local file system.

    Args:
        base_url (str): The base URL to fetch the data from.
        project_url (str): The URL of the project to be downloaded.
        path_prefix (str): A prefix to be added to the path where 
            the project will be downloaded.
    """
    path_to_project = os.path.join(path_prefix, project_url.split('/')[-1])
    os.makedirs(path_to_project, exist_ok=True)
    async with ClientSession() as session:
        semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
        await fetch_data(
            session,
            semaphore,
            base_url,
            path_to_project,
            project_url
        )
    calculate_sha256_for_directory(
        path_to_project,
        os.path.join(path_prefix, PATH_TO_RESULT)
    )


if __name__ == '__main__':
    asyncio.run(main(
        'https://gitea.radium.group',
        '/radium/project-configuration'
        )
    )
