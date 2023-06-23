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

config_file = 'config.ini'
msgs_file = 'messages.yaml'

class OpenAIChat:
    def __init__(self):
        self.data = []
        self.load_data()
        self.model = "text-davinci-002-render-sha"
        self.email = None
        self.password = None
        self.webdriver_path = 'C:\\Program Files\\Google\\Application\\Chrome\\chromedriver.exe'
        self.chrome_path = 'C:\\Program Files\\Google\\Application\\Chrome\\chrome.exe'
        self.user_data_dir = os.getenv('LOCALAPPDATA') + '\\Google\\Chrome\\User Data\\Default'
        self.access_token = None
        self.cookie = None

    def save_config(self):
        config = configparser.ConfigParser()
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
            self.webdriver_path = openai_section.get('webdriver_path')
            self.chrome_path = openai_section.get('chrome_path')
            self.user_data_dir = openai_section.get('user_data_dir')
        if(access_section):
            self.access_token = access_section.get('access_token', '')
            self.cookie = access_section.get('cookie', '')
            if(self.cookie):
                self.cookie = base64.b64decode(self.cookie).decode()

    def load_data(self):
        if os.path.isfile(msgs_file):
            with open(msgs_file, 'r') as file:
                self.data = yaml.safe_load(file)

    def save_data(self):
        with open(msgs_file, 'w') as file:
            yaml.dump(self.data, file)

    def get_second_last_chunk_text(self, data):
        chunks = data.split('\n\n')
        if len(chunks) < 3:
            return None
        second_last_chunk = chunks[-3]
        try:
            json_data = json.loads(second_last_chunk[6:])
            regex = re.compile(r'"id": "([^"]+)",.*"conversation_id": "([^"]+)"')
            match = regex.search(second_last_chunk)
            if match:
                id, conversation_id = match.group(1, 2)
                return [json_data['message']['content']['parts'], id, conversation_id]
        except json.JSONDecodeError as error:
            print('Error parsing JSON:', error)
        return None

    def extract_url(self, data):
        regex = re.compile(r'(https?://[^\s]+)')
        match = regex.search(data)
        if match:
            return match.group(0)
        return None

    def push_data(self, message, message_id, parent_thread_id):
        for thread in self.data:
            if thread['parent_thread_id'] == parent_thread_id:
                thread['messages'].append({'message_id': message_id, 'message': message})
                return
        self.data.append({'parent_thread_id': parent_thread_id, 'messages': [{'message_id': message_id, 'message': message}]})
        self.save_data()

    def reply_to_message(self, prompt, message_id, parent_thread_id, model):
        for thread in self.data:
            if thread['parent_thread_id'] == parent_thread_id:
                messages = thread['messages']
                for message in messages:
                    if message['message_id'] == message_id:
                        reply = self.reply(prompt, message_id, parent_thread_id)

    def reply(self, prompt, id, conversation_id):
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
            'parent_message_id': id,
            'conversation_id': conversation_id
        }
        response = requests.post('https://chat.openai.com/backend-api/conversation', headers=headers, json=payload)
        if response.status_code == 200:
            response_text = response.text
            data = self.get_second_last_chunk_text(response_text)
            self.push_data(data[0], data[1], data[2])
            return data[0]
        else:
            print('Error:', response.status_code)
            return None

    def chat(self, prompt):
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
            data = self.get_second_last_chunk_text(response_text)
            self.push_data(data[0], data[1], data[2])
            return data[0]
        else:
            print('Error:', response.status_code)
            return None

    def start(self, prompt):
        self.load_config()
        if not self.email or not self.password:
            self.email = input("Enter your email: ")
            self.password = input("Enter your password: ")
        if(not self.access_token or not self.cookie):
            chatToken = OpenAILoader(self.email, self.password, self.webdriver_path, self.chrome_path, self.user_data_dir)
            self.access_token, self.cookie = chatToken.login()
            self.save_config()
        result = self.chat(prompt)
        if(result):
            return result
        else:
            chatToken = OpenAILoader(self.email, self.password, self.webdriver_path, self.chrome_path, self.user_data_dir)
            self.access_token, self.cookie = chatToken.login()
            self.save_config()
            result = self.chat(prompt)
            return result
        return