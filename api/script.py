import os
import hashlib
import json
import telebot


FILE_SERVICE_CHUNK = 65_536

PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dir')  
os.chdir(PATH)

telegram_bot_token = '6400996360:AAFYAe3ho5qJOZUty81f41KXgJSeqhEosII'
bot = telebot.TeleBot(telegram_bot_token)
telegram_user_id = 310403765


def main():
    listdir = os.listdir('.')
    for file in listdir:
        if '.json' in file:
            with open(file) as f:
                data = json.load(f)
            video_filename = data['url'].split('/')[-1]
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            with open(video_filename, 'rb') as f:
                while d := f.read(FILE_SERVICE_CHUNK):
                    md5.update(d)
                    sha1.update(d)
            hash_data = {'md5': md5.hexdigest(), 'sha1': sha1.hexdigest()}
            if hash_data != data['hash']:
                bot.send_message(telegram_user_id, f'Файл {video_filename}: отличие хеша!')
            


if __name__ == '__main__':
    main()
