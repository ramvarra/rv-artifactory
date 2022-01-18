import io
import sys
import os
import logging
import asyncio

# add local src to path at the beginning to ensure its running against the local dev version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import afasync

print('Using afasync version: ', afasync.__version__)
AF_API_URL = 'http://jupiter.ramvarra.com:8081/artifactory'
AF_API_KEY = 'AKCp8k8sxbSxCDvSubFBjF1bg5LD8wYQzpwhrmqC4nXh3tN3jNFa7Nh5jQKxTGzVBggTb6oNA'
REPO = 'rv-test'

async def list_items(afi):
    ri = await afi.get_item_info(REPO, '/conc_io')
    logging.info("Repo has %d children", len(ri.file_children))
    it = f"{ri.path}/{ri.file_children[0]}"
    print('IT: ', it)

async def main():
    async with afasync.AFServer(AF_API_URL, api_key=AF_API_KEY) as afs:
        logging.info("AFI: %s", afs)
        await list_items(afs)
        d = await afs.system_info()
        print('SYSINFO: ', d)

    logging.info("main completed")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
