import streamlit as st
import asyncio
from client import post_data_from_txt

def page2():
    st.title('Загрузка данных')
    loader = st.selectbox('Выберите способ загрузки', ['', '.txt'])
    if loader == '.txt':
        uploaded_file = st.file_uploader('Выберите файл:', type=['txt'])
        if uploaded_file is not None:
            # data = uploaded_file.read().decode('utf-8')
            file_content = uploaded_file.read()
            file_to_send = {'name': uploaded_file.name, 'content': file_content, 'content_type': uploaded_file.type}

            async def main():
                return await post_data_from_txt('http://localhost:8000/api/v1/upload_file', file_to_send)

            st.write(asyncio.run(main()))