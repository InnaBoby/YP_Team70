import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import asyncio
import json


def items_to_list(func, url, col):
    # Получаем список имеющихся моделей
    async def list_models():
        return await func(url)

    items = asyncio.run(list_models())
    items = json.loads(items)
    list_items = []
    for item in items:
        list_items.append(item[col])
    return list_items


def hist_plot(top_words, q_words):

    df = pd.DataFrame({'Слово': top_words, 'Количество повторов в тексте': q_words})
    plt.title('Частота слов')
    f, axs = plt.subplots(figsize=(16, 10))
    sns.barplot(data=df, x=df['Количество повторов в тексте'], y=df['Слово'], ax = axs)
    plt.show()
    return f