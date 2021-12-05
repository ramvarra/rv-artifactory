import json
import yarl
from typing import Optional, Union
import logging
import asyncio
import aiohttp
import base64
from datetime import datetime, timezone


class AFItemInfo:
    @staticmethod
    def to_datetime(ts : str) -> datetime:
        #'2021-12-05T03:48:29.706Z'
        return datetime.fromisoformat(ts.rstrip('Z')).replace(tzinfo=timezone.utc)

    def __init__(self, json_resp : dict):
        logging.info("JSON: %s", json_resp)
        self.repo = json_resp['repo']
        self.path = json_resp['path']
        for attr_name, key in [('created', 'created'), ('modified', 'lastModified'), ('updated', 'lastUpdated')]:
            setattr(self, attr_name, self.to_datetime(json_resp.get(key)))
        children = json_resp.get('children')
        if children is not None:
            self.is_dir = True
            self.dir_children = [c['uri'].strip('/') for c in children if c['folder']]
            self.file_children = [c['uri'].strip('/') for c in children if not c['folder']]
        else:
            self.is_dir = False
            self.size = int(json_resp['size'])
            for name, value in json_resp.get('checksums', {}).items():
                setattr(self, name, value)
            self.mime_type = json_resp['mimeType']

    @property
    def is_file(self):
        return not self.is_dir

class AFInstance:
    def __init__(self, api_url: str,  auth: Optional[tuple[str, str]] = None,
                    api_key: Optional[str] = None):
        '''
        api_url: URL to involke api requests (e.g http[s]://host:8081/artifactory/)
        auth: tuple of username/password (optional)
        api_key: API key (optional).  Only one of the auth, api_key should be specified.
        '''
        api_url = api_url.rstrip('/')
        self.api_url = yarl.URL(api_url)
        self.api_path = yarl.URL(self.api_url.path)

        logging.info("API URL: %s", self.api_url)
        assert bool(auth) ^ bool(api_key), "One and only of the auth/api_key should be specified"
        if auth:
            headers = {'Authorization' : 'Basic %s' % base64.b64encode(":".join(auth))}
        else:
            headers = {'X-JFrog-Art-Api' : api_key}

        session_args = dict(headers=headers)
        self.session = aiohttp.ClientSession(self.api_url, **session_args)


    async def http_request(self, method : str, path : str):
        rpath = self.api_path / path
        logging.info("http_%s: %s", method, rpath)
        async with self.session.request(method, rpath) as r:
            r.raise_for_status()
            logging.info('Reponse Headers: %s', r.headers)
            content_type = r.headers.get('Content-Type')
            if content_type:
                return await (r.text() if content_type ==  'text/plain' else r.json())
            else:
                return await r.read()

    async def ping(self) -> str:
        return await self.http_request('GET', 'api/system/ping')

    async def system_info(self) -> str:
        return await self.http_request('GET', 'api/system')

    async def get_item_info(self, repo : str, path : Optional[str] = None) -> AFItemInfo:
        rpath = f"api/storage/{repo}" + (f"/{path}" if path else "")
        return AFItemInfo(await self.http_request('GET', rpath))

    async def delete_item(self, repo : str, path: str):
        assert path
        rpath = f"{repo}/{path}"
        await self.http_request('DELETE', rpath)
