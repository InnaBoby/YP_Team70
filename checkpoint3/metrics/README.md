__Hotpot:__
 - названия параграфов и номера предложений,  соответствующие ответу (supporting facts)
 - сам ответ (answer)
__Musique:__
 - Аналогично + есть вопросы, для которых нет ответа в контекстах, следовательно, модель должна так же распознать наличие/отсутствие ответа

__QA-metrics:__
 - Exact Match: ответ полностью совпадает с реальным ответом (или одним из)
 - F1-macro: пересечение всех верных ответов с предсказанием (по токенам)

__Text quality metrics:__
 - реализация тестирования другой LLM (библиотека deepeval с помощью gpt)
 1. Create a prompt by concatenating the evaluation steps with all the arguments listed in your evaluation steps (eg., if you’re looking to evaluate coherence for an LLM output, the LLM output would be a required argument).
 2. At the end of the prompt, ask it to generate a score between 1–5, where 5 is better than 1.
 3. (Optional) Take the probabilities of the output tokens from the LLM to normalize the score and take their weighted summation as the final result.
 Можно взять методику сравнения ответов из статьи про граф-раг:
 Our head-to-head measures computed using an LLM evaluator are as follows:
 
 • Comprehensiveness. How much detail does the answer provide to cover all aspects and details of the question?
 
 • Diversity. How varied and rich is the answer in providing different perspectives and insights on the question?
 
 • Empowerment. How well does the answer help the reader understand and make informed judgements about the topic?
 
 • Directness. How specifically and clearly does the answer address the question?
