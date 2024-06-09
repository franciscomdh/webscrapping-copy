"""
Archivo de funciones utiles que funcionan de forma global
"""


def word_to_lowercase(word):
    """Funcion para convertir la palabra a lowercase
    y eliminar los espacios

    :return: word_modified, str
    """
    word_modified = word.replace(" ", "")
    word_modified = word_modified.lower()
    return word_modified


def find_string(input_str, search_str):
    """Funcion para buscar todos los char en un string
    y guardar su posicion en una lista.

    Return
        - list: list_place_of_space

    """
    list_place_of_char = []
    length = len(input_str)
    index = 0
    while index < length:
        i = input_str.find(search_str, index)
        if i == -1:
            return list_place_of_char
        list_place_of_char.append(i)
        index = i + 1
    return list_place_of_char
