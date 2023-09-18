import os
from aiohttp import web
from datetime import datetime
import asyncio
from aiofile import async_open
import cgi
import hashlib
import cv2                               # для информации о видео
import ffmpeg                            # битрейт
import logging
import json


logging.basicConfig(filename='log.log', level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")

PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dir')  
os.chdir(PATH)

FILE_SERVICE_CHUNK = 65_536

API_TOKEN = 'TxYgyd4K5Zx4Ty0epKP8zxu50oiwZPLLT'             # сгенерировал случайный токен для Bearer-аунтефикации
DEL_API_TOKEN = 'LcDKEipcGlhNIjAcKHaMswFWvWIJtarJ9'         # а этот - для удаления

host = 'http://monitor.adstream.ru:3001'                    # для ссылки на файл


async def api_ping(request):
    return web.json_response({'msg': 'pong'}, status=200)


def auntefication(request, token):
    headers = dict(request.headers)
    autorization = headers.get('Authorization')
    return autorization == 'Bearer ' + token


async def api_file_download(request):
    if not auntefication(request, API_TOKEN):
        logging.warning('cant download file - auntefication failed!')
        return web.json_response({'error': 'auntefication failed'}, status=401)
    
    data = await request.json()
    filename = data['filename']
    if not os.path.exists(filename):
        logging.error('cant download file - file not found')
        return web.json_response({'error': 'file not found'}, status=400)

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': '*/*',
            'CONTENT-DISPOSITION': f'attachment;filename={filename}'
        }
    )
    await response.prepare(request)

    try:
        async with async_open(filename, 'rb') as f:
            chunk = await f.read(FILE_SERVICE_CHUNK)
            while chunk:
                await response.write(chunk)
                chunk = await f.read(FILE_SERVICE_CHUNK)
    except asyncio.CancelledError:
        logging.error('cant download file - download error')
        raise
    
    logging.info(f'file {filename} uploaded')
    return response


async def api_file_upload(request):
    if not auntefication(request, API_TOKEN):
        logging.warning('cant upload file - auntefication failed!')
        return web.json_response({'error': 'auntefication failed'}, status=401)
    
    _, params = cgi.parse_header(request.headers['CONTENT-DISPOSITION'])
    filename = params['filename']
    async with async_open(filename, 'bw') as afp:
        data = await request.read()
        await afp.write(data)
    await asyncio.sleep(0.5)
    logging.info(f'file {filename} uploaded')
    return web.json_response(get_file_info(filename), status=201)


def get_file_info(filename):
    params = dict()
    params['size'] = os.path.getsize(filename)

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while data := f.read(FILE_SERVICE_CHUNK):
            md5.update(data)
            sha1.update(data)
    params['hash'] = {'md5': md5.hexdigest(), 'sha1': sha1.hexdigest()}
    
    cap = cv2.VideoCapture(filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps

    width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    params['dimensions'] = {'width': width, 'height': height}
    params['duration'] = duration

    try:
        probe = ffmpeg.probe(filename)
        video_bitrate = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        bitrate = int(int(video_bitrate['bit_rate']) / 1000)
        params['bitrate'] = bitrate
    except Exception as e:
        params['bitrate'] = f'ERROR: {e}'
    
    params['url'] = host + '/videos/' + filename

    with open(filename.split('.')[0] + '.json', 'w') as f:          # запись данных в json
        json.dump(params, f)
    logging.info(f'file {filename} info: {params}')
    return params


async def api_file_remove(request):
    if not auntefication(request, DEL_API_TOKEN):
        logging.warning('cant remove file - auntefication failed!')
        return web.json_response({'error': 'auntefication failed'}, status=401)
    
    data = await request.json()
    filename = data['filename']
    if os.path.exists(filename):
        os.replace(filename, os.path.join('arh/', filename))
        json_filename = filename.split('.')[0] + '.json'
        os.replace(json_filename, os.path.join('arh/', json_filename))
        logging.info(f'file {filename} deleted')
        return web.json_response(status=201)
    else:
        logging.error(f'cant delete {filename}: file not found')
        return web.json_response({'error': 'file not found'}, status=400)


async def api_dir_list(request):
    if not auntefication(request, API_TOKEN):
        logging.warning('cant get files list - auntefication failed!')
        return web.json_response({'error': 'auntefication failed'}, status=401)
    
    listdir = os.listdir('.')
    logging.info(f'listdir: {listdir}')
    return web.json_response({'files': listdir}, status=200)


app = web.Application(client_max_size=50_000_000)                   # ВАЖНО!!! 50 000 000 - это максимальный размер файла в байтах, который можно отправить на сервер. ИСПРАВИТЬ на нужное число!!!
app.router.add_route('GET', '/api/ping', api_ping)
app.router.add_route('GET', '/api/video/download', api_file_download)
app.router.add_route('POST', '/api/video/upload', api_file_upload)
app.router.add_route('POST', '/api/video/remove', api_file_remove)
app.router.add_route('GET', '/api/video/list', api_dir_list)

app.router.add_static('/videos/', path=PATH, name='static')


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3000)
