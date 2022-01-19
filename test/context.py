import os
import sys
import pytest
import pytest_asyncio
import asyncio
import json

# insert local source path to test against it
# comment this line to test against installed version of afasync
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import afasync

TEST_CONFIG = "FM_NEXT"
CONFIG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))[TEST_CONFIG]

@pytest.fixture(scope="session")
def af_api_url():
    yield CONFIG['AF_API_URL']

@pytest.fixture(scope="session")
def af_api_key():
    env_var = CONFIG['AF_API_KEY']
    key = os.environ.get(env_var)
    assert key, f"Enviornment variable {env_var} not defined"
    yield key

@pytest.fixture(scope="session")
def af_test_repo():
    # need to use admin api to create it
    yield CONFIG['AF_TEST_REPO']

@pytest.fixture(scope="session")
def af_test_empty_repo():
    # need to use admin api to create it
    yield CONFIG['AF_TEST_EMPTY_REPO']    

# https://github.com/pytest-dev/pytest-asyncio/issues/68

@pytest.fixture(scope='session')
def event_loop(request):
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()    
    loop = asyncio.new_event_loop()    
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def af_server(af_api_url, af_api_key):
    async with afasync.AFServer(af_api_url, api_key=af_api_key) as afs:
        yield afs
