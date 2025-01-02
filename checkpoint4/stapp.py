import streamlit as st
import pandas as pd


st.title('Исследование RAG как увеличение контекста LLM моделей')
st.header('Шаг 1: Загрузка данных')
loader=st.selectbox("Выберите способ загрузки",
                    ['JSON', 'Текст'],
                    )
if loader == 'JSON':
    data_json=st.file_uploader('Выберите файл:', type=['json'])
    if data_json is not None:
        data=pd.read_json(data_json)
        st.dataframe(data.head())
elif loader == 'Текст':
    data_text=st.text_input('Введите текст...')
    if data_text is not None:
        data=data_text

st.header('Шаг 2: EDA, визуализация')
