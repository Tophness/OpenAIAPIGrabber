from ..loader import OpenAILoader
import re
import requests
import random
import uuid
import json
import configparser
import base64
import os
import yaml
import zipfile
import io
from win32com.client import Dispatch

config_file = 'config.ini'
msgs_file = 'messages.yaml'

class OpenAIChat:
    def __init__(self):
        self.data = []
        self.load_data()
        self.model = "text-davinci-002-render-sha"
        self.email = None
        self.password = None
        self.webdriver_path = ''
        self.chrome_path = ''
        self.user_data_dir = ''
        self.access_token = None
        self.cookie = None
        self.lastReply = None

    def download_and_extract_file(self, url):
        print("Downloading chrome..")
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(os.getcwd())
            print("Download succeeded.")
            return True
        else:
            print("Failed to download the file.")
            return False

    def get_version_via_com(self, filename):
        parser = Dispatch("Scripting.FileSystemObject")
        version = parser.GetFileVersion(filename)
        return version

    def get_chrome_install_location(self, p64bit):
        import winreg
        if p64bit:
            registry_path = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome Beta"
        else:
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome Beta"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
                return install_location
        except OSError:
            return None

    def download_chrome(self, p64bit):
        if(p64bit):
            if(self.download_and_extract_file('https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5790.24/win64/chrome-win64.zip')):
                self.chrome_path = os.path.join('chrome-win64', "chrome.exe")
        else:
            if(self.download_and_extract_file('https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5790.24/win32/chrome-win32.zip')):
                self.chrome_path = os.path.join('chrome-win32', "chrome.exe")

    def set_defaults(self):
        if(self.chrome_path == ''):
            import platform
            p64bit = platform.machine().endswith('64')
            chrome_beta_dir = self.get_chrome_install_location(p64bit)
            if(chrome_beta_dir):
                chrome_beta_path = os.path.join(chrome_beta_dir, "chrome.exe")
                if(self.get_version_via_com(chrome_beta_path) and self.get_version_via_com(chrome_beta_path).split('.')[0] > 114):
                    self.chrome_path = chrome_beta_path
                else:
                    self.download_chrome(p64bit)
            else:
                self.download_chrome(p64bit)
        if(self.user_data_dir == ''):
            chrome_types = ['Chrome Beta', 'Chrome Dev', 'Chrome']
            for chrome_type in chrome_types:
                localuserdir = os.path.join(os.getenv("LOCALAPPDATA"), "Google", chrome_type, "User Data", "Default")
                if(os.path.isdir(localuserdir)):
                    self.user_data_dir = localuserdir
                    return

    def save_config(self):
        config = configparser.ConfigParser()
        self.set_defaults()
        config['OpenAI'] = {
            'email': self.email,
            'password': self.password,
            'webdriver_path': self.webdriver_path,
            'chrome_path': self.chrome_path,
            'user_data_dir': self.user_data_dir
        }
        config['Access'] = {
            'access_token': self.access_token,
            'cookie': base64.b64encode(self.cookie.encode()).decode()
        }
        
        with open(config_file, 'w') as configfile:
            config.write(configfile)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(config_file)
        openai_section = None
        access_section = None
        if('OpenAI' in config):
            openai_section = config['OpenAI']
        if('Access' in config):
            access_section = config['Access']

        if(openai_section):
            self.email = openai_section.get('email')
            self.password = openai_section.get('password')
            self.webdriver_path = openai_section.get('webdriver_path', '')
            self.chrome_path = openai_section.get('chrome_path', '')
            self.user_data_dir = openai_section.get('user_data_dir', '')
        self.set_defaults()
        if(access_section):
            self.access_token = access_section.get('access_token', '')
            self.cookie = access_section.get('cookie', '')
            if(self.cookie):
                self.cookie = base64.b64decode(self.cookie).decode()

    def load_data(self):
        if os.path.isfile(msgs_file):
            with open(msgs_file, 'r') as file:
                self.data = yaml.safe_load(file)
        if(len(self.data) > 0):
            lastItem = self.data[-1]
            conversation_id = lastItem['conversation_id']
            last_message = lastItem['messages'][-1]
            parent_message_id = last_message['parent_message_id']
            message = last_message['message'][0]
            self.lastReply = {'conversation_id': conversation_id, 'parent_message_id': parent_message_id, 'message': message}

    def save_data(self):
        with open(msgs_file, 'w') as file:
            yaml.dump(self.data, file)

    def get_second_last_chunk_text(self, cdata):
        chunks = cdata.split('\n\n')
        if len(chunks) < 3:
            return None
        second_last_chunk = chunks[-3]
        try:
            json_data = json.loads(second_last_chunk[6:])
            regex = re.compile(r'"id": "([^"]+)",.*"conversation_id": "([^"]+)"')
            match = regex.search(second_last_chunk)
            if match:
                parent_message_id, conversation_id = match.group(1, 2)
                return [json_data['message']['content']['parts'], conversation_id, parent_message_id]
        except json.JSONDecodeError as error:
            print('Error parsing JSON:', error)
        return None

    def extract_url(self, udata):
        regex = re.compile(r'(https?://[^\s]+)')
        match = regex.search(udata)
        if match:
            return match.group(0)
        return None

    def deleteLast(self):
        return self.deletechat(self.lastReply['conversation_id'])

    def deletechat(self, id):
        url = 'https://chat.openai.com/backend-api/conversation/' + str(id)
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/event-stream',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Referer': 'https://chat.openai.com/',
            'Alt-Used': 'chat.openai.com',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Origin': 'https://chat.openai.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }
        payload = {
            'is_visible': False
        }
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            return None
        else:
            raise Exception(response.status_code)

    def push_data(self, message, conversation_id, parent_message_id):
        self.lastReply = {'conversation_id': conversation_id, 'parent_message_id': parent_message_id, 'message': message}
        for thread in self.data:
            if thread['conversation_id'] == conversation_id:
                thread['messages'].append({'parent_message_id': parent_message_id, 'message': message})
                self.save_data()
                return
        self.data.append({'conversation_id': conversation_id, 'messages': [{'parent_message_id': parent_message_id, 'message': message}]})
        self.save_data()

    def replyLast(self, prompt):
        return self.reply(prompt, self.lastReply['conversation_id'], self.lastReply['parent_message_id'])

    def reply_to_message(self, prompt, conversation_id, parent_message_id):
        for thread in self.data:
            if thread['conversation_id'] == conversation_id:
                messages = thread['messages']
                for message in messages:
                    if message['parent_message_id'] == parent_message_id:
                        reply = self.reply(prompt, conversation_id, parent_message_id)

    def iterate_threads_and_reply(self):
        for thread in self.data:
            conversation_id = thread['conversation_id']
            messages = thread['messages']
            for message in messages:
                parent_message_id = message['parent_message_id']
                content = message['message']
                print(content)
                reply_choice = input("Do you want to reply to this message? (y/n): ")
                if reply_choice.lower() == 'y':
                    prompt = input("Enter your reply prompt: ")
                    reply = self.reply(prompt, conversation_id, parent_message_id)
                    if reply:
                        print("Bot's Reply:", reply)
                print("------------------")

    def reply(self, prompt, conversation_id, parent_message_id, retry=False):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/event-stream',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Referer': 'https://chat.openai.com/',
            'Alt-Used': 'chat.openai.com',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Origin': 'https://chat.openai.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }
        payload = {
            'action': 'next',
            'messages': [{
                'content': {
                    'content_type': 'text',
                    'parts': [prompt]
                },
                'id': str(uuid.uuid4()),
                'role': 'user'
            }],
            'model': self.model,
            'parent_message_id': parent_message_id,
            'conversation_id': conversation_id
        }
        response = requests.post('https://chat.openai.com/backend-api/conversation', headers=headers, json=payload)
        if response.status_code == 200:
            response_text = response.text
            rdata = self.get_second_last_chunk_text(response_text)
            self.push_data(rdata[0], rdata[1], rdata[2])
            return rdata[0]
        else:
            if(retry):
                print('Error:', response.status_code)
                return None
            else:
                self.login()
                return self.reply(prompt, conversation_id, parent_message_id, True)

    def chat(self, prompt, autoDelete=False, retry=False):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/event-stream',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Referer': 'https://chat.openai.com/',
            'Alt-Used': 'chat.openai.com',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Origin': 'https://chat.openai.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }
        payload = {
            'action': 'next',
            'messages': [{
                'content': {
                    'content_type': 'text',
                    'parts': [prompt]
                },
                'id': str(uuid.uuid4()),
                'role': 'user'
            }],
            'model': self.model,
            'parent_message_id': str(uuid.uuid4())
        }
        response = requests.post('https://chat.openai.com/backend-api/conversation', headers=headers, json=payload)
        if response.status_code == 200:
            response_text = response.text
            rdata = self.get_second_last_chunk_text(response_text)
            if(autoDelete):
                self.deletechat(rdata[1])
            else:
                self.push_data(rdata[0], rdata[1], rdata[2])
            return rdata[0]
        else:
            if(retry):
                print('Error:', response.status_code)
                return None
            else:
                self.login()
                return self.chat(prompt, autoDelete, True)

    def login(self):
        self.load_config()
        if not self.email or not self.password:
            self.email = input("Enter your email: ")
            self.password = input("Enter your password: ")
        chatToken = OpenAILoader(self.email, self.password, self.webdriver_path, self.chrome_path, self.user_data_dir)
        self.access_token, self.cookie = chatToken.login()
        self.save_config()

    def start(self, prompt, autoDelete=False):
        self.load_config()
        if not self.email or not self.password:
            self.email = input("Enter your email: ")
            self.password = input("Enter your password: ")
        if(not self.access_token or not self.cookie):
            self.login()
        result = self.chat(prompt, autoDelete)
        return result