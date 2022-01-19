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

# TEST_CONFIG = "FM_NEXT"
TEST_CONFIG = "RV_HOME"

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
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def af_server(af_api_url, af_api_key):
    async with afasync.AFServer(af_api_url, api_key=af_api_key) as afs:
        yield afs

# Fixture with signle artifact to test the properties
@pytest.fixture(scope="session")
async def af_test_file(af_server, af_test_repo):
    file_path =  '/test_file.dat'
    data = b"Hello,World"
    result = await af_server.deploy_file(repo=af_test_repo, path=file_path, input_obj=data)
    assert result['size'] == str(len(data)), f"Upload failed"
    yield file_path
    result = await af_server.delete_item(repo=af_test_repo, path=file_path)
    assert len(result) == 0, f"Delete failed. Ret: {result}"
