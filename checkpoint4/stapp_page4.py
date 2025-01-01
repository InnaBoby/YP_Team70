import streamlit as st
from client import get_list_items, set_model
import asyncio
import json

def page4():
    st.title('Выбор модели')
    #Получаем список имеющихся моделей
    async def list_models():
        return await get_list_items('http://localhost:8000/api/v1/list_models')
    models = asyncio.run(list_models())
    models=json.loads(models)
    models_id=[]
    for model in models:
        models_id.append(model['model_id'])
    rag_model_id = st.selectbox('Выберите модель', tuple(models_id))

    # Получаем список имеющихся файлов
    async def list_files():
            return await get_list_items('http://localhost:8000/api/v1/list_files')
    files = asyncio.run(list_files())
    files = json.loads(files)
    files_names = []
    for file in files:
        files_names.append(file['retriever_id'])
    retriever_id = st.selectbox('Выберите файл', tuple(files_names))

    if st.button('Выбрать модель'):
        async def main():
            return await set_model('http://localhost:8000/api/v1/set_model', rag_model_id, retriever_id)

        st.write(asyncio.run(main()))

