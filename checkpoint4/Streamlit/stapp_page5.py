import streamlit as st
import asyncio
from Streamlit.client import invoke

def page5():
    st.title('Запрос')
    query=st.text_input('Введите запрос')
    if st.button('Отправить'):
        async def main():
            return await invoke('http://localhost:8000/api/v1/invoke', query)

        st.write(asyncio.run(main()))
