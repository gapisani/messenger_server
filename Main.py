import json, bcrypt, os, socket
from config import config
from chat_list import chat_list
from Log import Log

# TODO: Создать личные сообщения

class Server:
    def __init__(self, ip, port):
        Log("Initialization...").log()
        self.ip = ip
        self.port = port
        self.clients = {}
        Log("Starting server...").log()

    def resend_message(self, data_json, addres): # Пересыл сообщений от 1 пользователя для всех
        nickname = data_json["name"] # Получения имя от пользователя
        password = data_json["password"] # Получение пароля от пользователя
        if(self.password_check(nickname, password) and nickname.upper() != "SERVER"): # Если у пользователя верный пароль
            if(self.chat_check(data_json["chat"], nickname, addres, data_json["chat_key"])):
                chat = data_json["chat"]
                if(data_json["join"]): # Если это сообщение о входе
                    Log(f"{nickname}({addres[0]}:{addres[1]}) was connected!").successfully() # Выводим сообщение о подключении
                    result = f"{nickname} connected!" # Состовляем сообщение о подключении
                    nickname = "SERVER"

                elif(data_json["left"]): # Если это сообщение о выходе
                    for i in self.clients:
                        if(addres in self.clients[i]): # Если он есть в списке клиентов
                            self.clients[i].pop(addres) # То удаляем
                    result = f"{nickname} disconnected!" # Состовляем сообщение о выходе
                    nickname = "SERVER"

                else: # Иначе(Если это не сообщение о подключении и не сообщение о отключении)
                    msg = data_json["message"] # Получаем сообщение
                    result = f"{msg}" # Составяем сообщение
                for client in self.clients[chat]: # Перебираем клиентов
                    self.sock.sendto(json.dumps([{"nickname": nickname, "message": result, "chat":chat}]).encode('utf-8'), client) #Отсылаем сообщения клиентам
                Log(f"[{nickname}]: {result}", chat).chat() # Выводим результат в консоль
            else:
                self.sock.sendto(json.dumps([{"message":"Server hasn't this chat.", "chat":data_json["chat"]}]).encode("utf-8"), addres)
        else: #Если пароль не правильный
            self.sock.sendto(json.dumps([{"message":"Wrong password!", "chat":"#main"}]).encode("utf-8"), addres) # Отсылаем Клиенту сообщение о неправильном пароле


    def start(self): # Запуск сервера
        try:
            Log("Binding IP...").log()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Выделяем себе IP
            self.sock.bind((self.ip, self.port))
            Log("Running main server...").log()
            Log(f"Running server on {self.ip}:{self.port}!").successfully()
            while True: # Всегда
                data, addres = self.sock.recvfrom(1024) # Читаем сообщения от клиентов
                self.resend_message(json.loads(data.decode("utf-8")), addres) # Вызываем функцию пересыла сообщений
        except Exception as e: # Если произошла ошибка
            print(self.clients)
            for client in self.clients["#main"]: self.sock.sendto(json.dumps([{"message":"Server error", "chat":"#main"}]).encode("utf-8"), client) # Отсылаем сообщения о выходе клиентам
            self.sock.close() # Закрываем сокет
            raise(e) # Вызываем ошибку

    def password_check(self, user, password): # Функция проверки пароля
        if(not(os.path.isfile("Passwords.json"))): open("Passwords.json", "w").write("{}") # Если базы данных нет то создаем
        with open("Passwords.json", "r") as get_db: # Читаем базу данных
            db = json.load(get_db) # Загружаем базу данных
        if(user in db): # Если пользователь в базе данных
            if(bcrypt.checkpw(password.encode("utf-8"), db[user].encode("utf-8"))): return(True) # Проверяем пароль
            else: return(False)
        else: # Если пользователя нет в базе данных
            db[user] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") # Хешируем его пароль
            with open("Passwords.json", "w") as write_db: # Открываем базу данных для записи
                json.dump(db, write_db, sort_keys=True, indent=4) # Записываем туда обновленую версию
            return(True)

    def chat_check(self, chat, user, addres, key=None): # Функция проверки чата
        print(self.clients)
        if(chat in chat_list): # Если такой чат вообще есть на сервере
            if(chat not in self.clients):
                print("Chat is not in self.clients")
                self.clients[chat] = {}
            if(chat_list[chat]["join_key"]): # Если у чата есть ключ для входа
                if(key == chat_list[chat]["join_key"]): # Если он совпадает с тем что есть у пользователя
                    self.clients[chat][addres] = user
                    return(True) # Возвращаем True
                else: # Иначе(если он не совпадает с тем что у пользователя)
                    return(False) # Возвращаем False
            else: # Если у чата нет ключа для входа
                self.clients[chat][addres] = user
                return(True) # Так же возвращаем True
        else: # Если чата нет на сервере
            return(False) # возвращаем False

Server(config["ip"], config["port"]).start()
