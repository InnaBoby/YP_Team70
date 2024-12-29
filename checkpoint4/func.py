import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns



def hist_plot(top_words, q_words):

    df = pd.DataFrame({'Слово': top_words, 'Количество повторов в тексте': q_words})
    plt.title('Частота слов')
    f, axs = plt.subplots(figsize=(16, 10))
    sns.barplot(data=df, x=df['Количество повторов в тексте'], y=df['Слово'], ax = axs)
    plt.show()
    return f