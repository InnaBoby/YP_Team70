import streamlit as st
import asyncio
import logging
from client import invoke

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='./logs/streamlit.log',
    filemode='a',
)
logger = logging.getLogger('./logs/streamlit.log')
def page5():
    st.title('Запрос')
    query=st.text_input('Введите запрос')
    logger.info(f"Пользователь ввел запрос: {query}")
    if st.button('Отправить'):
        async def main():
            return await invoke('http://localhost:8000/api/v1/invoke', query)

        st.write(asyncio.run(main()))
