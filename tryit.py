import io
import sys
import os
import logging
import json
import asyncio

# add local src to path at the beginning to ensure its running against the local dev version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import afasync

print('Using afasync version: ', afasync.__version__)

TEST_CONFIG = "FM_NEXT"
CONFIG = json.load(open(os.path.join(os.path.dirname(__file__), 'test', 'config.json')))[TEST_CONFIG]

AF_API_URL = CONFIG['AF_API_URL']
AF_API_KEY = os.environ.get(CONFIG['AF_API_KEY'])
assert AF_API_KEY, f"API_KEY ENV var {CONFIG['AF_API_KEY']} not defined"
af_test_repo = CONFIG['AF_TEST_REPO']

async def list_items(afi):
    ri = await afi.get_item_info(repo=af_test_repo)
    logging.info("Repo has %d children", len(ri.file_children))
    it = f"{ri.path}/{ri.file_children[0]}"
    print('IT: ', it)

async def main():
    async with afasync.AFServer(AF_API_URL, api_key=AF_API_KEY) as af_server:
        logging.info("AFI: %s", af_server)        
        str_data = b"HELLO, WORLD"
        path = "/deploy-test/bytes.dat"
        result = await af_server.deploy_file(repo=af_test_repo, path=path, input_obj=str_data)
        print(result)
        result = await af_server.delete_item(repo=af_test_repo, path=path)
        print(result, type(result))
    logging.info("main completed")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(main()) 
    #loop = asyncio.new_event_loop()
    #loop.run_until_complete(main())
    #loop.close()
