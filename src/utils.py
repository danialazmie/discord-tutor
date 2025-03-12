import yaml
import logging
import os

def load_config(path: str = 'config.yaml'):
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_credentials(path: str = 'credentials.yaml'):
    with open(path, 'r') as f:
        credentials = yaml.safe_load(f)
    
    for k, v in credentials.items():
        os.environ[k] = v

    return list(credentials.keys())
        

def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)

    return logging.getLogger()
