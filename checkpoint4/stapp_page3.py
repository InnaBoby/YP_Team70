import streamlit as st
import asyncio
from client import create_model

def page3():
    st.title('Создание модели')
    model_id = st.text_input('Введите значение для model_id')
    config = {}
    for param in ['model', 'temperature', 'top_k', 'top_p', 'num_predict']:
        config[param] = st.text_input(f'Введите значение для {param}')
        req = {"model_id": model_id, "config": config}
    if st.button('Создать модель'):
        async def main():
            return await create_model('http://localhost:8000/api/v1/create_model', model_id, config)

        st.write(asyncio.run(main()))