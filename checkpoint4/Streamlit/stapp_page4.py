import streamlit as st
from func import items_to_list
from client import get_list_items, set_model
import asyncio

def page4():
    st.title('Выбор модели')
    # #Получаем список имеющихся моделей
    models_id = items_to_list(get_list_items,
                              'http://localhost:8000/api/v1/list_models',
                              'model_id')
    rag_model_id = st.selectbox('Выберите модель', tuple(models_id))

    # Получаем список имеющихся файлов
    files_names=items_to_list(get_list_items,
                              'http://localhost:8000/api/v1/list_files',
                              'retriever_id')
    retriever_id = st.selectbox('Выберите файл', tuple(files_names))

    if st.button('Выбрать модель'):
        async def main():
            return await set_model('http://localhost:8000/api/v1/set_model', rag_model_id, retriever_id)

        st.write(asyncio.run(main()))

