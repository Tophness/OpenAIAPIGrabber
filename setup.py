from setuptools import setup

setup(
    name='OpenAIAPIGrabber',
    version='1.0',
    author='Chris Malone',
    author_email='aussieelectronics2015@outlook.com',
    description='A python package for interacting with OpenAI API without needing API keys.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Tophness/OpenAIAPIGrabber',
    packages=['OpenAIAPIGrabber', 'OpenAIAPIGrabber.chat', 'OpenAIAPIGrabber.loader'],
    install_requires=[
        'selenium==4.10.0',
        'undetected-chromedriver==3.5.0',
        'requests==2.31.0',
        'PyYAML==6.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)