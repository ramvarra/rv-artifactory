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

#TEST_CONFIG = "FM_NEXT"
TEST_CONFIG = "RV_HOME"
CONFIG = json.load(open(os.path.join(os.path.dirname(__file__), 'test', 'config.json')))[TEST_CONFIG]

AF_API_URL = CONFIG['AF_API_URL']
AF_API_KEY = os.environ[CONFIG['AF_API_KEY']]
af_test_repo = CONFIG['AF_TEST_REPO']

async def list_items(afi):
    ri = await afi.get_item_info(repo=af_test_repo)
    logging.info("Repo has %d children", len(ri.file_children))
    it = f"{ri.path}/{ri.file_children[0]}"
    print('IT: ', it)

async def main():
    async with afasync.AFServer(AF_API_URL, api_key=AF_API_KEY) as af_server:
        lv = await af_server.get_version_license()
        print(lv)
        
    logging.info("main completed")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.get_event_loop().run_until_complete(main())
    #else:
    #    loop = asyncio.new_event_loop()
    #    loop.run_until_complete(main())
    #    loop.close()
