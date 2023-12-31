# OpenAIAPIGrabber
OpenAIAPIGrabber is a python package that provides functionality for interacting with OpenAI's chat API without needing API keys. It allows you to easily integrate OpenAI's chat capabilities into your own applications.

## Prerequisites

Before running the application, make sure you have the following prerequisites installed:

1. Install Python 3.x

2. Git

## Installation
You can install OpenAIAPIGrabber using pip. Run the following command:
```bash
pip install git+https://github.com/Tophness/OpenAIAPIGrabber
```
## Usage
Here's an example of how to use the `OpenAIChat` class from OpenAIAPIGrabber:
```python
from OpenAIAPIGrabber.chat import OpenAIChat
# Instantiate the OpenAIChat class
chat = OpenAIChat()
# Set up the prompt
prompt = "Your prompt here"
# Return the chat response
result = chat.start(prompt)
```
## Requirements
OpenAIAPIGrabber has the following requirements:
- selenium==4.10.0
- undetected-chromedriver==3.5.0
- requests==2.31.0

You can install these requirements using pip:
```bash
pip install -r requirements.txt
```

## License
This project is licensed under the [MIT License](LICENSE).
Make sure to include the `LICENSE` file in your repository as well if you choose to use the MIT License or any other license.
