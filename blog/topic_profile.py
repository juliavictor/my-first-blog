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

topic_profile_interface = {
    "Общество": ["00", "04", "26"],
    "Философия": ["02"],
    "История": ["03"],
    "Демография": ["05"],
    "Экономика": ["06", "71", "72", "80"],
    "Государство и право": ["10"],
    "Политика": ["11"],
    "Наука": ["12", "43", "81"],
    "Культура и искусство": ["13", "18"],
    "Педагогика": ["14"],
    "Психология": ["15"],
    "Языкознание": ["16"],
    "Литература": ["17"],
    "Журналистика": ["19"],
    "Информатика": ["20", "50"],
    "Религия": ["21"],
    "География": ["23", "39"],
    "Математика": ["27", "83"],
    "Кибернетика": ["28"],
    "Физика": ["29", "30", "45", "47", "58"],
    "Химия": ["31", "61"],
    "Биология": ["34", "62"],
    "Науки о земле": ["36", "37", "38", "52"],
    "Астрономия": ["41", "89"],
    "Энергетика": ["44"],
    "Полиграфия": ["60"],
    "Связь": ["49"],
    "Промышленность": ["53", "55", "59", "64"],
    "Питание": ["65"],
    "Архитектура": ["67"],
    "Сельское хозяйство": ["66", "68"],
    "Рыболовство": ["69"],
    "Вода": ["70"],
    "Транспорт": ["73"],
    "ЖКХ": ["75"],
    "Медицина": ["76"],
    "Спорт": ["77"],
    "Война": ["78"],
    "Управление": ["82"],
    "Стандартизация": ["84", "90"],
    "Изобретательство": ["85"],
    "Охрана труда": ["86"],
    "Экология": ["87"]
}

medium_vector = [0.11589088495575223, 0.014162212389380525, 0.02245353982300886, 0.036150707964601785, 0.007124247787610614, 0.010827256637168138, 0.015018672566371686, 0.009330442477876105, 0.020891858407079637, 0.01151716814159292, 0.03443752212389381, 0.017498141592920353, 0.02169035398230089, 0.04068194690265486, 0.03135619469026548, 0.007646548672566372, 0.015296283185840706, 0.008663362831858408, 0.019159292035398234, 0.03912902654867258, 0.021266106194690267, 0.0011730973451327432, 0.004017168141592919, 0.00542353982300885, 0.004637522123893803, 0.014239823008849559, 0.0051072566371681396, 0.01192132743362832, 0.003851238938053097, 0.02717681415929204, 0.0057841592920353955, 0.01452141592920354, 0.0029921238938053103, 0.006312920353982301, 0.006568761061946904, 0.010991592920353989, 0.026687345132743363, 0.0009753982300884954, 0.0009843362831858406, 0.007595663716814157, 0.00037946902654867256, 0.0027458407079646013, 0.013696371681415919, 0.0018122123893805318, 0.0008166371681415929, 0.007003185840707966, 0.019563451327433628, 0.006180265486725665, 0.006707699115044248, 0.0036311504424778747, 0.0022287610619469034, 0.00923946902654867, 0.016872123893805303, 0.0038755752212389387, 0.01641150442477876, 0.028903716814159295, 0.016429646017699116, 0.014109292035398225, 0.009048849557522127, 0.01586796460176992, 0.046471858407079646, 0.051249203539823, 0.0033078761061946897, 0.001033274336283186, 0.0015146902654867254, 0.0011190265486725663, 0.0028900000000000006, 0.0037287610619469035, 0.0031603539823008837]


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
def form_topic_rating(vector, dictionary, shortened = None):
    # Приводим в соответствие ключи (названия категорий) и значения тематического профиля
    i = 0
    dict = dictionary.copy()

    for key in dict:
        dict[key] = np.round(vector[i], 5)
        i += 1

    # Укороченная форма названия категорий ГРНТИ (--)
    if shortened:
        short_dict = {}
        i = 0

        for key in dict:
            short_dict[key[0:2]] = np.round(vector[i], 5)
            i += 1

        return short_dict

    # Сортируем получившийся словарь по значению
    sorted_dict = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    return sorted_dict


def topic_profile_ui(dict):
    user_prof = {}

    for key in topic_profile_interface:
        user_prof[key] = 0
        for category in topic_profile_interface[key]:
            user_prof[key] += dict[category]

    return user_prof