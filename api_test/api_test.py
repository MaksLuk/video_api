import asyncio
import aiofiles as aiofiles
import aiohttp as aiohttp
import requests
import filecmp
import pytest
import time


SERVER_URL = 'http://0.0.0.0:3000'


async def file_sender(file_name, chunksize=65_536):
    async with aiofiles.open(file_name, "rb") as f:
        chunk = await f.read(chunksize)
        while chunk:
            yield chunk
            chunk = await f.read(chunksize)


async def upload_file():
    headers = {'CONTENT-DISPOSITION': f'attachment; filename="k1.mp4"', 'Authorization': 'Bearer TxYgyd4K5Zx4Ty0epKP8zxu50oiwZPLLT'}
    async with aiohttp.ClientSession() as session:
        async with session.post(SERVER_URL + '/api/video/upload', headers=headers, data=file_sender("k1.mp4"), ssl=False) as resp:
            print(await resp.text())


def download_file():
    f = open('k2.mp4',"wb")
    response = requests.get(SERVER_URL + '/api/video/download', headers={'Authorization': 'Bearer TxYgyd4K5Zx4Ty0epKP8zxu50oiwZPLLT'}, json={'filename': 'k1.mp4'})
    for chunk in response.iter_content(chunk_size=65_536): 
        if chunk: 
            f.write(chunk)
    f.close()


def delete_file():
    response = requests.post(SERVER_URL + '/api/video/remove', headers={'Authorization': 'Bearer LcDKEipcGlhNIjAcKHaMswFWvWIJtarJ9'}, json={'filename': 'k1.mp4'})


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(upload_file())
    download_file()
    assert filecmp.cmp('k1.mp4', 'k2.mp4')
    time.sleep(5)
    delete_file()
