import asyncio
import csv
import os
import shutil
from unittest.mock import Mock, AsyncMock

import aiohttp
import pytest

from scrapper.main import (
    PATH_TO_RESULT,
    calculate_sha256_for_directory,
    main,
    save_file,
    fetch_data,
)


@pytest.fixture
def semaphore():
    return asyncio.Semaphore(3)


@pytest.fixture
def base_url():
    return "https://gitea.radium.group"


@pytest.fixture
def project_url():
    return "/radium/project-configuration"


@pytest.fixture
def wrong_base_url():
    return "https://example.com"


@pytest.fixture
def wrong_project_url():
    return "/test.txt"


@pytest.fixture
def temp_dir():
    new_dir = os.path.join(os.getcwd(), "test_dir")
    os.makedirs(new_dir, exist_ok=True)
    yield new_dir
    shutil.rmtree(new_dir)


@pytest.mark.asyncio
async def test_save_file(semaphore, temp_dir, base_url):
    url = "/project-configuration/raw/branch/master/README.md"
    async with aiohttp.ClientSession() as s:
        await save_file(s, semaphore, base_url, url, temp_dir)

    filename = url.split("/")[-1]
    assert os.path.isfile(f"{temp_dir}/{filename}")


@pytest.mark.asyncio
async def test_save_file_connection_error(
    wrong_base_url, wrong_project_url, semaphore, temp_dir
):
    session = Mock(spec=aiohttp.ClientSession)
    session.get = AsyncMock(
        side_effect=aiohttp.client_exceptions.ClientConnectorError(
            Mock(), OSError("Error message")
        )
    )
    assert (
        await save_file(
            session, semaphore, wrong_base_url, wrong_project_url, temp_dir
        )
        == None
    )


def test_calculate_sha256_for_directory(temp_dir):
    path_to_file = os.path.join(temp_dir, "mock")
    calculate_sha256_for_directory("tests/mock_data", path_to_file)

    with open(path_to_file, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for i, row in enumerate(reader):
            if i == 1:
                assert (
                    row[1]
                    == "f896b2614dc15394c6c1e90731635f418c4b09b168718c6a3ff52d00c3720ba8"
                )
                break


@pytest.mark.asyncio
async def test_fetch_data_connection_error(
    wrong_base_url, wrong_project_url, semaphore, temp_dir
):
    session = Mock(spec=aiohttp.ClientSession)
    session.get = AsyncMock(
        side_effect=aiohttp.client_exceptions.ClientConnectorError(
            Mock(), OSError("Error message")
        )
    )
    assert (
        await fetch_data(
            session, semaphore, wrong_base_url, temp_dir, wrong_project_url
        )
        == None
    )


def test_main_func(temp_dir, base_url, project_url):
    asyncio.run(main(base_url, project_url, temp_dir))

    assert os.path.isfile(f"{temp_dir}/{PATH_TO_RESULT}")
