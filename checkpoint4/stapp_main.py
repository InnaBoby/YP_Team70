import streamlit as st
from stapp_page1 import *
from stapp_page2 import *
from stapp_page3 import *
from stapp_page4 import *
from stapp_page5 import *
from stapp_page6 import *
from stapp_page7 import *
import os

if not os.path.isdir('logs'):
    os.mkdir('logs')

pg = st.navigation([
    st.Page(page1, title="Главная", icon="🔥"),
    st.Page(page2, title="Загрузка данных", icon=":material/download:"),
    st.Page(page3, title="Создание модели", icon=":material/extension:"),
    st.Page(page4, title="Выбор модели", icon=":material/cards:"),
    st.Page(page5, title="Запрос", icon=":material/question_mark:"),
    st.Page(page6, title='EDA, Визуализация',icon=":material/visibility:"),
    st.Page(page7, title='Очистка', icon=":material/delete:"),
])

pg.run()