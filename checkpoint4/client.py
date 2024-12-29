import aiohttp
import asyncio


async def post_data_from_txt(endpoint, file):
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        form.add_field(name='file', value=file['content'], filename=file['name'], content_type=file['content_type'])
        async with session.post(endpoint, data=form) as response:
             return await response.text()


async def create_model(endpoint, model_id, config):
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json={'model_id': model_id, 'config': config}) as response:
            return await response.text()


async def get_list_items(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.text()


async def set_model(endpoint, rag_model_id, retriever_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json={'rag_model_id': rag_model_id, 'retriever_id': retriever_id}) as response:
            return await response.text()


async def invoke(endpoint, query):
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json={'query': query}) as response:
            return await response.text()


async def delete_item(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.delete(endpoint) as response:
            return await response.text()


async def delete_list_items(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.delete(endpoint) as response:
            return await response.text()