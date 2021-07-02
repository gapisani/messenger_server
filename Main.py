import json, bcrypt, os, socket, sys
from config import config
from chat_list import chat_list
from Log import Log

# TODO: Создать личные сообщения

APP_PATH = os.path.dirname(os.path.abspath(__file__))

class Server:
    def __init__(self, ip, port):
        Log("Initialization...").log()
        self.ip = ip
        self.port = port
        self.clients = {}
        if(not(os.path.isdir(APP_PATH+"/save_data"))):
            os.mkdir(APP_PATH+"/save_data")
        if(not(os.path.isfile(APP_PATH+"/save_data/passwords.json"))):
            open(APP_PATH+"/save_data/passwords.json", "w").write("{}")
        if(not(os.path.isfile(APP_PATH+"/save_data/message_history.json"))):
            open(APP_PATH+"/save_data/message_history.json", "w").write("[]")

    def resend_message(self, data_json, addres): # Пересыл сообщений от 1 пользователя для всех
        nickname = data_json["name"] # Получения имя от пользователя
        password = data_json["password"] # Получение пароля от пользователя
        if(self.password_check(nickname, password) and nickname.upper() != "SERVER"): # Если у пользователя верный пароль
            if(self.chat_check(data_json["chat"], nickname, addres, data_json["chat_key"])):
                chat = data_json["chat"]
                if(data_json["join"]): # Если это сообщение о входе
                    self.sock.sendto(json.dumps(self.load_messages_from_history()).encode("utf-8"), addres)
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
                final_message = [{"nickname": nickname, "message": result, "chat":chat}]
                for client in self.clients[chat]: # Перебираем клиентов
                    self.sock.sendto(json.dumps(final_message).encode('utf-8'), client) #Отсылаем сообщения клиентам
                Log(f"[{nickname}]: {result}", chat).chat() # Выводим результат в консоль
                self.write_message_to_history(final_message)
            else:
                self.sock.sendto(json.dumps([{"message":"Server hasn't this chat.", "chat":data_json["chat"], "nickname": "SERVER"}]).encode("utf-8"), addres)
        else: #Если пароль не правильный
            self.sock.sendto(json.dumps([{"message":"Wrong password!", "chat":"#main", "nickname":"SERVER"}]).encode("utf-8"), addres) # Отсылаем Клиенту сообщение о неправильном пароле
        


    def start(self): # Запуск сервера
        Log("Starting server...").log()
        try:
            Log("Binding IP...").log()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Выделяем себе IP
            self.sock.bind((self.ip, self.port))
            Log("Running main server...").log()
            Log(f"Running server on {self.ip}:{self.port}!").successfully()
            while True: # Всегда
                data, addres = self.sock.recvfrom(1024) # Читаем сообщения от клиентов
                self.resend_message(json.loads(data.decode("utf-8")), addres) # Вызываем функцию пересыла сообщений
                self.__str__ = f"Server on {self.ip}:{self.port}, {len(self.clients['#main'])} online." # Обновление статуса сервера
        except Exception as e: # Если произошла ошибка
            print("Error:", e)
            self.stop()

    def password_check(self, user, password): # Функция проверки пароля
        with open(APP_PATH+"/save_data/passwords.json", "r") as get_db: # Читаем базу данных
            db = json.load(get_db) # Загружаем базу данных
        if(user in db): # Если пользователь в базе данных
            if(bcrypt.checkpw(password.encode("utf-8"), db[user].encode("utf-8"))): return(True) # Проверяем пароль
            else: return(False)
        else: # Если пользователя нет в базе данных
            db[user] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") # Хешируем его пароль
            with open(APP_PATH+"/save_data/passwords.json", "w") as write_db: # Открываем базу данных для записи
                json.dump(db, write_db, sort_keys=True, indent=4) # Записываем туда обновленую версию
            return(True)

    def chat_check(self, chat, user, addres, key=None): # Функция проверки чата
        if(chat in chat_list): # Если такой чат вообще есть на сервере
            if(chat not in self.clients):
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

    def command(self):
        pass

    def write_message_to_history(self, message):
        history_file = APP_PATH+"/save_data/message_history.json"

        db = json.load(open(history_file, "r"))
        db += message
        json.dump(db, open(history_file, "w"))

    def load_messages_from_history(self):
        history_file = APP_PATH+"/save_data/message_history.json"
        db = json.load(open(history_file, "r"))
        return(db)

    def stop(self):
        for client in self.clients["#main"]: self.sock.sendto(json.dumps([{"message":"Server error", "chat":"#main", "nickname":"SERVER"}]).encode("utf-8"), client) # Отсылаем сообщения о выходе клиентам
        self.sock.close() # Закрываем сокет
        sys.exit()

s = Server(config["ip"], config["port"])
try:
    s.start()
except KeyboardInterrupt:
    s.stop()