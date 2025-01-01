import streamlit as st
import asyncio
import json
import logging
from client import get_list_items, delete_item, delete_list_items

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='./logs/streamlit.log',
    filemode='a',
)
logger = logging.getLogger('./logs/streamlit.log')

def page7():
    st.title('Очистка')

    remove_model = st.checkbox('Удалить модель')
    if remove_model:
        # Получаем список имеющихся моделей
        async def list_models():
            return await get_list_items('http://localhost:8000/api/v1/list_models')

        models = asyncio.run(list_models())
        models = json.loads(models)
        models_id = []
        for model in models:
            models_id.append(model['model_id'])

        model_id = st.selectbox('Выберите модель, которую хотите удалить', tuple(models_id))
        logger.info(f"Пользователь хочет удалить модель: {model_id}")
        if st.button('Удалить'):
            async def main():
                return await delete_item(f'http://localhost:8000/api/v1/remove_model/{model_id}')

            st.write(asyncio.run(main()))
            logger.info(f"Модель: {model_id} удалена")

    remove_file=st.checkbox('Удалить файл')
    if remove_file:
        # Получаем список имеющихся файлов
        async def list_files():
            return await get_list_items('http://localhost:8000/api/v1/list_files')

        files = asyncio.run(list_files())
        files = json.loads(files)
        files_names = []
        for file in files:
            files_names.append(file['retriever_id'])

        file = st.selectbox('Выберите файл', tuple(files_names))
        logger.info(f"Пользователь хочет удалить файл: {file}")
        if st.button('Удалить'):
            async def main():
                return await delete_item(f'http://localhost:8000/api/v1/remove_file/{file}')
            st.write(asyncio.run(main()))
            logger.info(f"Файл: {model_id} удален")


    remove_all_models=st.checkbox('Удалить все модели')
    if remove_all_models:
        # Получаем список имеющихся моделей
        async def list_models():
            return await get_list_items('http://localhost:8000/api/v1/list_models')

        models = asyncio.run(list_models())
        models = json.loads(models)
        models_id = []
        for model in models:
            models_id.append(model['model_id'])
        st.write('Будут удалены следующие модели:', models_id)
        if st.button('OK'):
            async def main():
                return await delete_list_items('http://localhost:8000/api/v1/remove_all_models')
            st.write(asyncio.run(main()))
            logger.info(f"Все модели удалены")

    remove_all_files=st.checkbox('Удалить все файлы')
    if remove_all_files:
        # Получаем список имеющихся файлов
        async def list_files():
            return await get_list_items('http://localhost:8000/api/v1/list_files')

        files = asyncio.run(list_files())
        files = json.loads(files)
        files_names = []
        for file in files:
            files_names.append(file['retriever_id'])

        st.write('Будут удалены следующие файлы:', files_names)
        logger.info(f"Пользователь хочет удалить файлы: {files_names}")
        if st.button('OK'):
            async def main():
                return await delete_list_items('http://localhost:8000/api/v1/remove_all_files')

            st.write(asyncio.run(main()))
            logger.info(f"Все файлы удалены")



