#!/usr/bin/python

import threading
import subprocess
import time
from pynput import keyboard
import pyttsx3
import pyatspi
from print_text_at_offset import on_caret_move

# Инициализируем движок TTS
engine = pyttsx3.init('espeak')

#Словари для преобразований
EN_TO_RU = {
    '`': 'ё', 'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
    'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ', 'a': 'ф', 
    's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 
    'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 
    'b': 'и', 'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '~': 'Ё', 
    '@': '"', '#': '№', '$': ';', '^': ':', '&': '?', '|': '/', '+': '+', 
    '<': 'б', '>': 'ю', 'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 
    'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
    'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О',
    'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С',
    'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь'
}

char, word, line, ctrl_pressed, n_char, n_word, n_line = None, None, None, None, None, None, None

def get_keyboard_layout():
    try:
        # Вызываем xkb-switch для получения текущей раскладки
        return subprocess.check_output('xkb-switch -p', shell=True).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return 'us'  # Вернуть 'us' по умолчанию, если команда не выполнена

def on_press(key):
    # Получаем текущую раскладку клавиатуры
    current_layout = get_keyboard_layout()    
    try:
        key_char = key.char if hasattr(key, 'char') else str(key)[4:]
        if current_layout == 'ru' and key_char in EN_TO_RU:
            engine.setProperty('voice', 'russian')
            key_char = EN_TO_RU[key_char]
        else:
            engine.setProperty('voice', 'english-us')
        print(f'Key {key_char} pressed')
        global ctrl_pressed
        # Проверяем, нажата ли клавиша Ctrl
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = True
        global char, word, line, n_char, n_word, n_line
        time.sleep(0.5)
        if key_char in ['right', 'left'] and ctrl_pressed and not word == None:
            engine.say(str(n_word))
            char, word, line = None, None, None
        elif key_char in ['right'] and not char == None:
            engine.say(str(char))
        elif key_char in ['left'] and not char == None:
            engine.say(str(n_char))  
            char, word, line = None, None, None
        elif key_char in ['up', 'down'] and not line == None:
            engine.say(str(line))
            char, word, line = None, None, None
        else:
            engine.say(str(key_char))
        last_key = key_char
        engine.runAndWait()
    except AttributeError:
        pass  # Ничего не делаем, если у ключа нет атрибута 'char'

def on_release(key):
    global ctrl_pressed
    # Проверяем, отпущена ли клавиша Ctrl
    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        ctrl_pressed = False
    if key == keyboard.Key.esc:
        # При нажатии клавиши Escape прекращаем прослушивание
        pyatspi.Registry.stop()
        return False

def on_caret_move(event):
    if event.source and event.source.getRole() == pyatspi.ROLE_TERMINAL:
        return
    print_text_at_offset(event.source, event.detail1)

def print_text_at_offset(obj, offset):
  text = obj.queryText()
  global char, word, line, n_char, n_word, n_line
  char, word, line = n_char, n_word, n_line
  n_char, char_start_offset, char_end_offset = text.getTextAtOffset(offset, pyatspi.TEXT_BOUNDARY_CHAR)
  n_word, word_start_offset, word_end_offset = text.getTextAtOffset(offset, pyatspi.TEXT_BOUNDARY_WORD_START)
  n_line, line_start_offset, line_end_offset = text.getTextAtOffset(offset, pyatspi.TEXT_BOUNDARY_LINE_START)
  print("Char:%s \nWord:%s \nLine:%s " % (char, word, line))
  #print(last_key)


def on_key_input(event):
    print(event.event_string)
#
# # Создаем и запускаем слушатель клавиатуры
def start_pynput_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def start_pyatspi_listener():
    pyatspi.Registry.registerEventListener(on_caret_move, "object:text-caret-moved")
    pyatspi.Registry.start()

if __name__ == "__main__":
    # Создаем поток для слушателя pynput
    pynput_thread = threading.Thread(target=start_pynput_listener)
    pynput_thread.start()

    # Создаем поток для слушателя pyatspi
    pyatspi_thread = threading.Thread(target=start_pyatspi_listener)
    pyatspi_thread.start()

    # Дожидаемся завершения работы потоков
    pynput_thread.join()
    pyatspi_thread.join()