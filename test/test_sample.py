import asyncio
import pytest
import re
from datetime import datetime, timezone

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

async def test_empty_repo(af_server, af_test_repo):
    info = await af_server.get_item_info(repo=af_test_repo)
    assert info
    assert info.is_dir
    assert len(info.file_children) == 0
    assert len(info.dir_children) == 0
    for attr_name in ['created', 'modified', 'updated']:
        assert hasattr(info, attr_name)
        t = getattr(info, attr_name)
        assert isinstance(t, datetime)
        assert t.tzinfo is timezone.utc
