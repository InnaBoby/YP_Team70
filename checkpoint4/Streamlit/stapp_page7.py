fastapiimport streamlit as st
import asyncio
import json
import logging
from Streamlit.func import items_to_list
from Streamlit.client import get_list_items, delete_item, delete_list_items

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
        models_id = items_to_list(get_list_items,
                                  'http://fastapi:8000/api/v1/list_models',
                                  'model_id')
        model_id = st.selectbox('Выберите модель, которую хотите удалить', tuple(models_id))
        logger.info(f"Пользователь хочет удалить модель: {model_id}")
        if st.button('Удалить'):
            async def main():
                return await delete_item(f'http://fastapi:8000/api/v1/remove_model/{model_id}')

            st.write(asyncio.run(main()))
            logger.info(f"Модель: {model_id} удалена")

    remove_file=st.checkbox('Удалить файл')
    if remove_file:
        # Получаем список имеющихся файлов
        files_names = items_to_list(get_list_items,
                                    'http://fastapi:8000/api/v1/list_files',
                                    'retriever_id')
        file = st.selectbox('Выберите файл', tuple(files_names))
        logger.info(f"Пользователь хочет удалить файл: {file}")
        if st.button('Удалить'):
            async def main():
                return await delete_item(f'http://fastapi:8000/api/v1/remove_file/{file}')
            st.write(asyncio.run(main()))
            logger.info(f"Файл: {file} удален")

    remove_all_models=st.checkbox('Удалить все модели')
    if remove_all_models:
        # Получаем список имеющихся моделей
        models_id = items_to_list(get_list_items,
                                  'http://fastapi:8000/api/v1/list_models',
                                  'model_id')
        st.write('Будут удалены следующие модели:', models_id)
        logger.info(f"Пользователь хочет удалить файлы: {models_id}")
        if st.button('OK'):
            async def main():
                return await delete_list_items('http://fastapi:8000/api/v1/remove_all_models')
            st.write(asyncio.run(main()))
            logger.info(f"Все модели удалены")

    remove_all_files=st.checkbox('Удалить все файлы')
    if remove_all_files:
        # Получаем список имеющихся файлов
        files_names = items_to_list(get_list_items,
                                    'http://fastapi:8000/api/v1/list_files',
                                    'retriever_id')
        st.write('Будут удалены следующие файлы:', files_names)
        logger.info(f"Пользователь хочет удалить файлы: {files_names}")
        if st.button('OK'):
            async def main():
                return await delete_list_items('http://fastapi:8000/api/v1/remove_all_files')

            st.write(asyncio.run(main()))
            logger.info(f"Все файлы удалены")



