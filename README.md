св# conf3
Этот проект представляет эмулятор командной строки.

## Задание 
Разработать эмулятор для языка оболочки ОС. Необходимо сделать работу 
эмулятора как можно более похожей на сеанс shell в UNIX-подобной ОС. 
Эмулятор должен запускаться из реальной командной строки, а файл с 
виртуальной файловой системой не нужно распаковывать у пользователя. 
Эмулятор принимает образ виртуальной файловой системы в виде файла формата 
zip. Эмулятор должен работать в режиме GUI. 
Ключами командной строки задаются: 
• Имя пользователя для показа в приглашении к вводу. 
• Путь к архиву виртуальной файловой системы. 
• Путь к лог-файлу. 
• Путь к стартовому скрипту. 
Лог-файл имеет формат json и содержит все действия во время последнего 
сеанса работы с эмулятором. Для каждого действия указан пользователь. 
Стартовый скрипт служит для начального выполнения заданного списка 
команд из файла. 
Необходимо поддержать в эмуляторе команды ls, cd и exit, а также 
следующие команды: 
1. mv. 
2. chmod. 
Все функции эмулятора должны быть покрыты тестами, а для каждой из 
поддерживаемых команд необходимо написать 2 теста.



##Команда для запуска программы 
python main.py -u Sergey -a filesys.zip -l log.json -s empty.txt

##Тестирование

![img.png](img.png)

![img_1.png](img_1.png)

![img_2.png](img_2.png)