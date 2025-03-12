from .prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_RAG_USER_PROMPT

from haystack import Pipeline
from haystack.dataclasses import ChatMessage, Document
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.retrievers.pinecone import PineconeEmbeddingRetriever
from haystack_integrations.document_stores.pinecone import PineconeDocumentStore
from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator

from pydantic import BaseModel

from utils import load_config

CONFIG = load_config('config.yaml')

MODEL_CONFIGS = CONFIG['model_configs']
ANTHROPIC_KWARGS = MODEL_CONFIGS['anthropic']['generation_kwargs']
OPENAI_KWARGS = MODEL_CONFIGS['openai']['generation_kwargs']


class Model:

    def __init__(
        self,
        model: str = 'anthropic',
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: list = [],
        generation_kwargs: dict = {}
    ):
        self.SYSTEM_PROMPT = system_prompt

        # Resolve generation_kwargs
        if generation_kwargs == {} and model == 'anthropic':
            generation_kwargs = ANTHROPIC_KWARGS
        elif generation_kwargs == {} and model == 'openai':
            generation_kwargs == OPENAI_KWARGS

        if model == 'anthropic':
            self.generator = AnthropicChatGenerator(
                model=MODEL_CONFIGS['anthropic']['model'],
                generation_kwargs=generation_kwargs
            )
        elif model == 'openai':
            self.generator = OpenAIChatGenerator(
                model=MODEL_CONFIGS['openai']['model'], 
                generation_kwargs=generation_kwargs
            )

        self.memory = [ChatMessage.from_system(self.SYSTEM_PROMPT)]
        self.use_rag = False

    def prompt(self, text: str):
        self.memory.append(ChatMessage.from_user(text))
        response = self.generator.run(self.memory)['replies'][-1]
        return response
        

class ChatSession(Model):

    def __init__(
        self,
        model: str = 'anthropic',
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: list = [],
        generation_kwargs: dict = {}
    ):
        super().__init__(model=model, system_prompt=system_prompt, tools=tools, generation_kwargs=generation_kwargs)

    def run(self, query: dict):

        if self.use_rag:
            documents = self.rag_pipeline.run({'text_embedder': {'text': query}})['retriever']['documents']
            query = self.user_prompt_builder.run(documents=documents, question=query)['prompt']

        self.memory.append(ChatMessage.from_user(query))
        response = self.generator.run(self.memory)['replies'][-1]
        self.memory.append(response)

        return response


    def add_document_store(self, document_store, template = None):

        if template:
            self.user_prompt_builder = PromptBuilder(template)
        else:
            self.user_prompt_builder = PromptBuilder(DEFAULT_RAG_USER_PROMPT)

        self.rag_pipeline = Pipeline()
        self.rag_pipeline.add_component('text_embedder', OpenAITextEmbedder())
        self.rag_pipeline.add_component('retriever', PineconeEmbeddingRetriever(document_store=document_store, top_k=15))
        self.rag_pipeline.connect('text_embedder.embedding', 'retriever.query_embedding')

        self.use_rag = True

    def remove_document_store(self):

        del self.rag_pipeline
        del self.user_prompt_builder

        self.use_rag = False

    def reset_session(self):
        self.memory = [ChatMessage.from_system(self.SYSTEM_PROMPT)]
        self.remove_document_store()
