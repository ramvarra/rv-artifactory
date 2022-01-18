import asyncio
import pytest
import re

from .context import *

def test_version():
    assert hasattr(afasync, '__version__')
    assert re.match(r'\d+\.\d+\.\d+', afasync.__version__)

async def test_ping(af_server):
    result = await af_server.ping()
    assert result == 'OK'

async def test_system_info(af_server):
    result = await af_server.system_info()
    assert 'Artifactory Info' in result
    assert 'artifactory.version' in result

async def test_non_existing_repo(af_server):
    with pytest.raises(afasync.ItemNotFoundError):
        await af_server.get_item_info(repo='non_existing_repo')
