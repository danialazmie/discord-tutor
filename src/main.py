import discord
from utils import load_config, load_credentials
import logging
from llm import ChatSession
from llm.prompts import EDUCATOR_SYSTEM_PROMPT_ANTHROPIC
from disc.parser import parse_message
import os

load_credentials()

stream_handler = logging.StreamHandler()
logger = logging.getLogger('discord')

CONFIG = load_config('config.yaml')
ACTIVE_MODEL = CONFIG['active_model']
MODEL_CONFIGS = CONFIG['model_configs']

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

session = None

class Content:

    def __init__(self, text: str = None, images: list = [], model: str = 'openai'):
        self.text = text
        self.images = images
        self.model = model

        self.dct = [
            {
                'type': 'text',
                'text': text
            }
        ]

        if len(images) > 0:
            for image in images:
                self.dct.append(
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image
                        }
                    }
                )

        return
    
    def build(self):

        if self.model=='openai':
            pass

        if self.model=='anthropic':
            content = [
                {
                'type': 'text',
                'text': self.text
                }
            ]

            for image in self.images:
                content.append(
                    {
                        'type': 'image',
                        'source': {
                            'type': 'url',
                            'url': image
                        }
                    }
                )

            self.dct = content

        return self.dct

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    global session

    if message.content == '!reset':
        session = None
        logger.info('Session reset')
        await message.channel.send('`Session reset`')
        return

    logger.info(f'{message.channel} | {message.author}: {message.content}')

    if str(message.channel) == 'chatbot':

        if session is None:

            session = ChatSession(
                ACTIVE_MODEL,
                system_prompt=EDUCATOR_SYSTEM_PROMPT_ANTHROPIC
                # system_prompt=CONFIG[ACTIVE_MODEL][]
            )

            # session = ChatSession(
            #     model='o3-mini',
            #     system_prompt=EDUCATOR_SYSTEM_PROMPT_ANTHROPIC,
            #     generation_kwargs={'reasoning_effort': 'high', 'seed': 112233}
            # )

        # Build content

        image_urls = []

        if len(message.attachments) > 0:
            for attachment in message.attachments:
                if attachment.content_type.startswith('image'):
                    image_urls.append(attachment.url)

        # content = Content(message.content, ['data:image/webp;base64,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'])
        content = Content(message.content, image_urls, model='anthropic')
        # content = Content(message.content)

        print(content.build())

        response = session.run(content.build())
        # response = session.run(message.content)
        print(response.text)
        print(response.meta)

        # input_tokens = response.meta["usage"]["prompt_tokens"]
        # reasoning_tokens = response.meta["usage"]["completion_tokens_details"].reasoning_tokens
        # output_tokens = response.meta["usage"]["completion_tokens"] - reasoning_tokens

        # logger.info(f'Input tokens: {input_tokens}')
        # logger.info(f'Reasoning tokens: {reasoning_tokens}')
        # logger.info(f'Output tokens: {output_tokens}')
        # print(response.meta)
        response_text = response.text


        chunks = parse_message(response_text)

        for chunk in chunks:
            if chunk.image:
                await message.channel.send(chunk.text, file=discord.File(chunk.image))
                os.remove(chunk.image)
            else:
                await message.channel.send(chunk.text)



client.run(
    token=os.environ.get('DISCORD_BOT_TOKEN'),
    log_handler=stream_handler, 
    log_level=logging.INFO
)
