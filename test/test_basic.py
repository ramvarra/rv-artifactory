import asyncio
import pytest
import re
from datetime import datetime, timezone
import hashlib

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

async def test_empty_repo(af_server, af_test_empty_repo):
    info = await af_server.get_item_info(repo=af_test_empty_repo)
    assert info
    assert info.is_dir
    assert len(info.file_children) == 0
    assert len(info.dir_children) == 0
    for attr_name in ['created', 'modified', 'updated']:
        assert hasattr(info, attr_name)
        t = getattr(info, attr_name)
        assert isinstance(t, datetime)
        assert t.tzinfo is timezone.utc

async def util_deploy(af_server, af_test_repo, path, input_obj, size, md5_checksum):
    result = await af_server.deploy_file(repo=af_test_repo, path=path, input_obj=input_obj)
    for key in ('repo', 'path', 'created', 'createdBy', 'downloadUri', 'mimeType', 'size', 'checksums', 'uri'):
        assert key in result
    assert result['path'] == path
    assert result['repo'] == af_test_repo
    assert result['size'] == size
    assert result['checksums']['md5'] == md5_checksum
    result = await af_server.delete_item(repo=af_test_repo, path=path)
    assert len(result) == 0

async def test_deploy_str(af_server, af_test_repo):
    data = "HELLO, WORLD"
    path = "/deploy-test/string.txt"
    size = len(data.encode('utf-8'))
    md5_checksum = hashlib.md5(data.encode('utf-8')).hexdigest()
    await util_deploy(af_server, af_test_repo, path, data, size, md5_checksum)

async def test_deploy_bytes(af_server, af_test_repo):
    data = b"HELLO, WORLD IN BYTES"
    path = "/deploy-test/bytes.dat"
    size = len(data)
    md5_checksum = hashlib.md5(data).hexdigest()
    await util_deploy(af_server, af_test_repo, path, data, size, md5_checksum)

async def test_deploy_text_file(af_server, af_test_repo, tmp_path):
    data = "HELLO, WORLD"
    file_path = tmp_path / "text_file.txt"
    with open(file_path, "w") as fd:
        fd.write(data)
    data = open(file_path, "rb").read()
    size = len(data)
    md5_checksum = hashlib.md5(data).hexdigest()
    path = "/deploy-test/text_file.txt"
    await util_deploy(af_server, af_test_repo, path, open(file_path, "r"), size, md5_checksum)
    os.remove(file_path)

async def test_deploy_binary_file(af_server, af_test_repo, tmp_path):
    data = b"HELLO, WORLD BINARY DATA"
    file_path = tmp_path / "binary_file.dat"
    with open(file_path, "wb") as fd:
        fd.write(data)
    size = len(data)
    md5_checksum = hashlib.md5(data).hexdigest()
    path = "/deploy-test/text_file.txt"
    await util_deploy(af_server, af_test_repo, path, open(file_path, "rb"), size, md5_checksum)
    os.remove(file_path)

async def test_read_empty_props(af_server, af_test_repo, af_test_file):
    props = await af_server.get_properties(repo=af_test_repo, path=af_test_file)
    assert props == {}

async def test_version_license(af_version_license):
    for k in ('version', 'licenseType'):
        assert af_version_license[k]
    if vt := af_version_license.get('validThrough'):
        assert isinstance(vt, datetime)
    assert re.match(r'\d+\.\d+\.\d+$', af_version_license['version'])

async def test_concurrent_deploy(af_server, af_test_repo, af_concurrent_test_folder):
    n = 100
    results = []
    exp_results = []

    for i in range(1, n+1):
        path = af_concurrent_test_folder + f"/CONCURRENT_TEST_{i:00d}.txt"
        data = f"HELLO,WORLD {i} " + "X" * i
        size = len(data.encode('utf-8'))
        md5_checksum = hashlib.md5(data.encode('utf-8')).hexdigest()
        exp_result = {'size': size, 'md5': md5_checksum}
        exp_results.append(exp_result)
        r = await af_server.deploy_file(repo=af_test_repo, path=path, input_obj=data)
        print(r)
        results.append(r)

    for exp, act in zip(exp_results, results):
        assert exp['size'] == act['size']
        assert exp['md5'] == act['checksums']['md5']

    # await the tasks
