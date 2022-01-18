import os
import sys
import pytest
import pytest_asyncio
import asyncio
# insert local source path to test against it
# comment this line to test against installed version of afasync
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import afasync

AF_API_URL = 'http://jupiter.ramvarra.com:8081/artifactory'
AF_API_KEY = 'AKCp8k8sxbSxCDvSubFBjF1bg5LD8wYQzpwhrmqC4nXh3tN3jNFa7Nh5jQKxTGzVBggTb6oNA'
AF_TEST_REPO = 'rv-test'

@pytest.fixture(scope="session")
def af_api_url():
    yield AF_API_URL

@pytest.fixture(scope="session")
def af_api_key():
    yield AF_API_KEY

@pytest.fixture(scope="session")
def af_test_repo():
    yield AF_TEST_REPO

# https://github.com/pytest-dev/pytest-asyncio/issues/68
@pytest.fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def af_server(af_api_url, af_api_key):
    async with afasync.AFServer(af_api_url, api_key=af_api_key) as afs:
        yield afs
