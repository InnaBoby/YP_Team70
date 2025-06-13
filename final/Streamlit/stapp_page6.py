import streamlit as st
from wordcloud import WordCloud
import nltk
from gensim.models import Word2Vec
from nltk import FreqDist
import pandas as pd
import numpy as np
from Streamlit.func import *
from sklearn.manifold import TSNE
from bokeh.io import output_notebook
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure, show

def page6():
    st.title('EDA, Визуализация')
    data=None
    loader = st.selectbox("Выберите способ загрузки", ['', '.txt', 'Текст'])
    if loader == '.txt':
        uploaded_file = st.file_uploader('Выберите файл:', type=['txt'])
        if uploaded_file is not None:
            data=uploaded_file.read().decode('utf-8')
    elif loader == 'Текст':
        data = st.text_input('Введите текст...')

    if data is not None:
        st.write(f'Длина текста {len(data)} символов')
        st.write(f'Количество слов в тексте {len(data.split())}')
        data = data.lower()
        st.write('Облако слов')
        cloud = WordCloud(width=800, height=400, random_state=42,
                          background_color='white', colormap='Set2', collocations=False
                          ).generate(data)
        st.image(cloud.to_array())

        tokens = data.split()
        model_w2v = Word2Vec([tokens], vector_size=300, window=5, min_count=1, workers=-1)

        N = st.select_slider('Показать TOP N слов',
                             options=range(0, len(tokens))
                             )
        if N:
            fd = FreqDist()
            fd.update(tokens)
            top_words = []
            q_words = []
            st.dataframe(pd.DataFrame(fd.most_common(N),
                                      columns=['Слово', 'Количество повторов в тексте']
                                      ).set_index('Слово')
                             )
            for word, q in fd.most_common(N):
                top_words.append(word)
                q_words.append(q)

            if st.toggle('показать гистограмму распределения ТОП-30 слов'):
                st.write(hist_plot(top_words[:30], q_words[:30]))

            top_words_vec = model_w2v.wv[top_words]
            tsne = TSNE(n_components=2, random_state=0)
            top_words_tsne = tsne.fit_transform(top_words_vec)

            output_notebook()
            p = figure(tools="pan,wheel_zoom,reset,save",
                       toolbar_location="above",
                       title="word2vec T-SNE for most common words")

            source = ColumnDataSource(data=dict(x1=top_words_tsne[:, 0],
                                                x2=top_words_tsne[:, 1],
                                                names=top_words))

            p.scatter(x="x1", y="x2", size=8, source=source)

            labels = LabelSet(x="x1", y="x2", text="names", y_offset=6,
                              text_font_size="8pt", text_color="#555555",
                              source=source, text_align='center')
            p.add_layout(labels)

            st.bokeh_chart(p)
