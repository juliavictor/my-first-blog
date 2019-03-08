import pymorphy2
import re
from scipy import spatial
import numpy as np
import operator
import json
import math

# Для работы также необходимо установить пакет для русского языка
# pip install -U pymorphy2-dicts-ru

morph = pymorphy2.MorphAnalyzer()


# Косинусное расстояние
def compare_vectors(vec1, vec2):
    # Если один из векторов полностью состоит из нулей, возвращаем 0
    if not np.any(vec1) or not np.any(vec2):
        result = 0
    else:
        result = 1 - spatial.distance.cosine(vec1, vec2)

    if math.isnan(result):
        result = 0

    return result


# Нормализуем весь текст: на выходе строка из нормализованных слов
def normalize_doc(doc):
    doc = re.sub(r'^https?:\/\/.*[\r\n]*', '', doc, flags=re.MULTILINE)
    word_list = re.sub("[^\w]", " ", doc).split()
    normalized_text = ""
    for word in word_list:
        normalized_word = morph.parse(word)[0].normal_form
        normalized_text += normalized_word + " "
    return normalized_text


# Сравнение двух списков
def count_similar(one, two):
    count = 0
    for item in one:
        for item1 in two:
            if item == item1:
                count += 1
    return count


# Нормализация вектора документа: сумма элементов становится равной 1
def normalize_vector(vec):
    if sum(vec) == 0:
        return vec
    ratio = 1 / sum(vec)
    norm_vec = [np.round(i * ratio,5) for i in vec]
    return norm_vec


def normalize_vector_full(vec):
    if sum(vec) == 0 or sum(vec) == -0:
        norm_vec = []
        for element in vec:
            norm_vec.append(1/len(vec))
        return norm_vec
    ratio = 1 / sum(vec)
    norm_vec = [(i * ratio) for i in vec]
    return norm_vec

# Подсчет количества упоминаний ключевого слова в словаре
def count_keyword_in_dict(keyword, dictionary):
    count = 0
    for i in dictionary:
        for word in dictionary[i]:
            if word == keyword:
                count += 1
    return count


# Формирование вектора документа
# doc - исходный документ
# dict - словарь
# norm_keywords - флаг, определяющий использование улучшенного алгоритма расчета веса ключевого слова
# debug - флаг отладки (выводит на экран найденные ключевые слова)
def form_doc_vector(doc, dict, norm_keywords, debug=None):
    vector = []
    doc = " " + doc + " "

    # Просматриваем каждую тему в словаре
    for i in dict:
        matches = 0

        for key_word in dict[i]:
            count = doc.count(" " + key_word + " ")
            # print(count)
            # print(len(doc.split(" " + key_word + " "))-1)

            # Если флаг norm_keywords = True:
            #   делим вес слова на количество его упоминаний в словаре
            if norm_keywords:
                keywords_count = count_keyword_in_dict(key_word, dict)
                if keywords_count > 0:
                    count /= keywords_count

            # Отладочная информация (найденные в тексте ключевые слова)
            if count > 0 and debug:
                print(key_word + " (" + str(count) + ")", )

            # Для биграмм увеличиваем количество слов на 2
            if len(key_word.split()) == 2:
                count *= 2

            matches += count

        # Отладочная информация (название категории)
        if matches > 0 and debug:
            print(" – " + i + "\n")

        # Значение = отношение кол-ва найденных слов / ко всем словам текста
        value = matches / len(doc)

        vector.append(value)

    return normalize_vector(vector)


# Возвращает список категорий, отсортированных по убыванию значения
# На вход - значение уже рассчитанного вектора и словарь с нужными ключами
def form_topic_rating(vector, dictionary):
    # Приводим в соответствие ключи (названия категорий) и значения тематического профиля
    i = 0
    dict = dictionary.copy()

    for key in dict:
        dict[key] = np.round(vector[i], 5)
        i += 1

    # Сортируем получившийся словарь по значению
    sorted_dict = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    return sorted_dict
