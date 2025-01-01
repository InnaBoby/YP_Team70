import streamlit as st
import asyncio
from client import create_model
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='./logs/streamlit.log',
    filemode='a',
)
logger = logging.getLogger('./logs/streamlit.log')

def page3():
    st.title('Создание модели')
    model_id = st.text_input('Введите значение для model_id')
    logger.info(f"Создание модели: {model_id}")
    config = {}
    for param in ['model', 'temperature', 'top_k', 'top_p', 'num_predict']:
        config[param] = st.text_input(f'Введите значение для {param}')
        req = {"model_id": model_id, "config": config}
    if st.button('Создать модель'):
        async def main():
            return await create_model('http://localhost:8000/api/v1/create_model', model_id, config)

        st.write(asyncio.run(main()))