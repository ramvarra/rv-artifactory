import yarl
from typing import Optional, Tuple, Union, Any
import logging
import aiohttp
import base64
from datetime import datetime, timezone

# Custo Exceptions
class APIError(Exception):
    def __init__(self, method, api, status, error):
        super().__init__(f"API '{method} {api}' failed with {status} - '{error}'")

class NoPropertiesFound(Exception):
    pass

class ItemNotFoundError(FileNotFoundError):
    pass

class AFItemInfo:
    @staticmethod
    def to_datetime(ts : str) -> datetime:
        #'2021-12-05T03:48:29.706Z'
        return datetime.fromisoformat(ts.rstrip('Z')).replace(tzinfo=timezone.utc)

    def __init__(self, *, json_resp : dict) -> None:
        assert 'repo' in json_resp, f"Missing repo key in json_resp: {json_resp}"
        assert 'path' in json_resp, f"Missing path key in json_resp: {json_resp}"
        self.repo = json_resp['repo']
        self.path = json_resp['path'].strip("/")
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


class AFServer:
    def __init__(self, api_url: str,  *, auth: Optional[tuple[str, str]] = None,
                    api_key: Optional[str] = None) -> None:
        '''
        api_url: URL to involke api requests (e.g http[s]://host:8081/artifactory/)
        auth: tuple of username/password (optional)
        api_key: API key (optional).  Only one of the auth, api_key should be specified.
        '''
        api_url = api_url.rstrip('/')
        self.api_url = yarl.URL(api_url)
        self.api_path = yarl.URL(self.api_url.path)

        logging.debug("API URL: %s", self.api_url)
        assert bool(auth) ^ bool(api_key), "One and only of the auth/api_key should be specified"
        if auth:
            headers = {'Authorization' : 'Basic %s' % base64.b64encode(":".join(auth))}
        else:
            headers = {'X-JFrog-Art-Api' : api_key}

        session_args = dict(headers=headers)
        self.session = aiohttp.ClientSession(self.api_url, **session_args)

    
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.session.close()
        

    async def close_session(self):
        await self.session.close()

    @staticmethod
    def success(status):
        return 200 <= status < 300

    @staticmethod
    def check_for_errors(status: int, data: dict) -> Optional[str]:
        if AFServer.success(status):
            return None
        if errors := data.get('errors'):
            assert isinstance(errors, list), f"Errors expected to be list, but got {errors}"
            return "".join(e.get('message') for e in errors)
        return str(data)

    async def http_request(self, method : str, path : str, **kwargs) -> Tuple[int, Any]:
        rpath = self.api_path / path
        logging.info("http_%s: %s", method, rpath)
        async with self.session.request(method, rpath, **kwargs) as r:
            #logging.info('Reponse Headers: %s', r.headers)
            content_type = r.headers.get('Content-Type', '')
            if 'json' in content_type:
                data = await r.json()
                if errstr := self.check_for_errors(r.status, data):
                    data = errstr
                if r.status == 404:
                    if 'Unable to find item' in data:
                        raise ItemNotFoundError(path)
                    elif "No properties could be found." in data:
                        raise NoPropertiesFound()
            elif 'text' in content_type:
                data = await r.text()
            else:
                data = await r.read()

            if not self.success(r.status):
                raise APIError(method, path, r.status, data)
            return r.status, data

    async def ping(self) -> str:
        status, data = await self.http_request('GET', 'api/system/ping')
        return data

    async def system_info(self) -> str:
        status, data = await self.http_request('GET', 'api/system')
        return data

    async def get_item_info(self, repo : str, path : Optional[str] = None) -> AFItemInfo:
        assert repo
        rpath = f"api/storage/{repo}" + (f"/{path.strip('/')}" if path else "")
        status, data = await self.http_request('GET', rpath)
        return AFItemInfo(json_resp=data)

    async def delete_item(self, repo : str, path: str) -> Union[str, bytes]:
        '''
        Returns either "" or b"" (depending on the type of path)
        '''
        assert repo and path
        rpath = f"{repo}/{path}"
        status, result = await self.http_request('DELETE', rpath)
        return result

    async def deploy_file(self, repo : str, path: str, input_obj) -> None:
        '''
        Deploy data in input_obj to repo/path
        input_obj = file like object (that has read() method) or bytes or str
        '''
        assert repo and path
        rpath = f"{repo}/{path}"
        if hasattr(input_obj, 'read'):
            input_obj = input_obj.read()
        if isinstance(input_obj, str):
            input_obj = input_obj.encode('utf-8')
        assert isinstance(input_obj, bytes), f"Input must be bytes"
        status, result = await self.http_request('PUT', rpath, data=input_obj)
        return result

    async def get_properties(self, repo : str, path: str) -> dict:
        assert repo and path
        rpath = f"api/storage/{repo}/{path}"
        try:
            status, data = await self.http_request('GET', rpath, params='properties')
        except NoPropertiesFound:
            return {}
        assert 'properties' in data, f"Missing properties key in {data}"
        return data['properties']

    # Ack: https://github.com/devopshq/artifactory/blob/master/artifactory.py
    @staticmethod
    def escape_chars(s: str) -> str:
        """
        Performs character escaping of comma, pipe and equals characters
        """
        assert isinstance(s, str), f"bad non str value in property '{s}'"
        return "".join(["\\" + ch if ch in "=|," else ch for ch in s])

    @staticmethod
    def encode_properties(parameters: dict) -> str:
        """
        Performs encoding of url parameters from dictionary to a string. It does
        not escape backslash because it is not needed.
        See: http://www.jfrog.com/confluence/display/RTF/Artifactory+REST+API#ArtifactoryRESTAPI-SetItemProperties
        """
        result = []

        for key, value in parameters.items():
            if isinstance(value, (list, tuple)):
                value = ",".join([AFInstance.escape_chars(x) for x in value])
            else:
                value = AFServer.escape_chars(value)

            result.append("=".join((key, value)))

        return ";".join(result)

    async def set_properties(self, repo: str, path: str, props: dict, recursive: bool) -> None:
        assert repo and path
        params = {'properties': self.encode_properties(props)}
        if not recursive:
            params['recursive'] = "0"
        rpath = f"api/storage/{repo}"
        status, data = await self.http_request('PUT', rpath, params=params)

