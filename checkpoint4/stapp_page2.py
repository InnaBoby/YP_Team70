import streamlit as st
import asyncio
import logging
from client import post_data_from_txt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='./logs/streamlit.log',
    filemode='a',
)
logger = logging.getLogger('./logs/streamlit.log')

def page2():
    st.title('Загрузка данных')
    loader = st.selectbox('Выберите способ загрузки', ['', '.txt'])
    logger.info(f"Выбранный способ загрузки {loader}")
    if loader == '.txt':
        uploaded_file = st.file_uploader('Выберите файл:', type=['txt'])
        if uploaded_file is not None:
            # data = uploaded_file.read().decode('utf-8')
            file_content = uploaded_file.read()
            file_to_send = {'name': uploaded_file.name, 'content': file_content, 'content_type': uploaded_file.type}
            logger.info(f"Загружен файл с именем: {file_to_send['name']}")

            async def main():
                return await post_data_from_txt('http://localhost:8000/api/v1/upload_file', file_to_send)

            st.write(asyncio.run(main()))
        else:
            logger.warning("Пользователь не выбрал файл")

    