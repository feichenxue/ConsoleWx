#!/data/software/python3.7/bin/python3
# -*- coding: UTF-8 -*-

import re
import os
import sys
import time
import json
import redis
import pymongo
import requests
import datetime
from queue import Queue
from wxpy import *
import threading
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion.word_completer import WordCompleter



class ChatRobot(object):
    def __init__(self):
        # 实例化，并登录微信
        SysType = sys.platform
        if SysType == "win32":
            bot = Bot(cache_path=True)
        else:
            bot = Bot(console_qr=2,cache_path=True)

        #基本设置
        bot.messages.max_history = 10000
        bot.auto_mark_as_read = False
        saveurl = "http://172.16.9.74:18090/wxdata/"
        robotapi_url = "http://10.1.10.77:5000/cc"  

        #获取当前登录用户名
        myself = re.sub(">", "", str(bot.self).split()[1])
        allfriends = bot.friends()
        allgroup = bot.groups()
        friendslist = []
        groupslist = []

        #所有朋友
        for i in allfriends:
            name = re.sub(">", "", str(i).split()[1])
            friendslist.append(name)


        #所有群聊
        for g in allgroup:
            groupname = re.sub(">", "", str(g).split()[1])
            groupslist.append(groupname)

        alllist = friendslist + groupslist        
        NameCompleter = WordCompleter(alllist, ignore_case=True)


        #初始化数据
        self.bot = bot
        self.myself = myself
        self.saveurl = saveurl
        self.SysType = SysType
        self.friendslist = friendslist
        self.groupslist = groupslist
        self.NameCompleter = NameCompleter
        self.robotapi_url = robotapi_url
        self.console = "console"
        self.msgtypelist = ["Picture","Recording","Attachment","Video"]
        

    #连接redis
    def con_redis(self, host='172.16.9.74', port='16379', db=3):
        pool = redis.ConnectionPool(host=host, port=port, db=db)
        r = redis.Redis(connection_pool=pool)
        return r

    def get_user(self, userstr):
        name = userstr
        result = re.sub(">", "", str(name).split()[1])
        return result


    #连接mongoDB,并且返回集合对象
    def con_mongoDB(self, host='172.16.9.74', port=17974):
        mongo_client = pymongo.MongoClient(host=host, port=port)
        mon_db = mongo_client['WeChat_chat']
        mo_collection = mon_db['history_msg']
        return mo_collection


    #类似于生产者
    def push_to_redis(self, savmsg):
        try:
            r = self.con_redis()
            r.lpush('chat_msg', savmsg)
            print("OK, End!!")
        except Exception as e:
            print(e)

    # 类似于消费者
    def get_redis_msg(self):
        r = self.con_redis()
        result = r.brpop('chat_msg', 1)
        if result:
            return result[1].decode()
        else:
            return False

    def save_to_mongodb(self, insert_content, savedb=True, infomsg=True):
        try:
            if savedb:
                mo_collection = self.con_mongoDB()
                result = mo_collection.insert_one(insert_content)
                if infomsg:
                    print("save mongodb success!!!")
        except Exception as e:
            print(e)

    def robot_api(self, inputstr):
        try:
            request_data = {'input': inputstr}
            api_url = self.robotapi_url
            result = requests.get(api_url,data=request_data)
            return json.loads(result.text)
        except Exception as e:
            print(e)


    def my_robot_api(self, inputmsg):
        q = Queue()
        myrobot = self.bot.mps().search("飞沉血")[1]
        myrobot.send(inputmsg)
        @self.bot.register(myrobot)
        def get_msg(msg):
            print("自动返回的消息为: ", msg)
            q.put(msg.text)

        send_msg = q.get()
        return send_msg


    #接收某个好友或群聊消息并且用我的接口自动回复
    def Receive_Relpy_My_Msg(self, who):
        @self.bot.register(who)
        def print_one_messages(msg):
            if self.SysType == "win32":
                print("\n[{} \033[1;31m接收到的消息 ↙\033[0m]: ".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            else:
                print("\n[{} \033[1;31m接收到的消息 ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            if msg.type != "Text":
                reply_content = self.my_robot_api("不是文字消息！")
            else:                
                reply_content = self.my_robot_api(msg.text)
            msg.reply(reply_content)
            replay_datetime = self.get_datetime()
            print("自动回复的消息为：[{0}]: {1}".format(replay_datetime, reply_content))
            
        self.bot.join()


    #接收某个好友或群聊消息并且自动回复
    def Receive_Relpy_Msg(self, who):
        @self.bot.register(who, except_self=False)
        def print_one_messages(msg):
            if self.SysType == "win32":
                print("\n[{} \033[1;31m接收到的消息 ↙\033[0m]: ".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            else:
                print("\n[{} \033[1;31m接收到的消息 ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
       
            reply_content = self.robot_api(msg.text)
            msg.reply(reply_content)
            replay_datetime = self.get_datetime()
            print("自动回复的消息为：[{0}]: {1}".format(replay_datetime, reply_content))
            
        self.bot.join()


    #接收全部消息并且自动回复 此处还需要优化
    def ReceiveAll_Relpy_Msg(self):
        @self.bot.register(except_self=False)
        def print_one_messages(msg):
            if self.SysType == "win32":
                print("\n[{} \033[1;31m接收到的消息 ↙\033[0m]: ".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            else:
                print("\n[{} \033[1;31m接收到的消息 ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))           
            if msg.text not in self.msgtypelist:        
                reply_content = self.robot_api(msg.text)
                msg.reply(reply_content)
                replay_datetime = self.get_datetime()
                print("自动回复的消息为：[{0}]: {1}".format(replay_datetime, reply_content))
            else:
                msg.reply("呜呜呜，此消息我还没法回答！！！")
        self.bot.join()

    #仅仅打印全部消息，不做任何其它操作
    def Receive_All(self, savedb=True, infomsg=True):
        """
        简单示例：
        test = ChatRobot()
        test.Receive_All()
        savedb == True 时，将保存消息到mongodb, 为False时，不保存，默认为保存消息
        infomsg 默认为True，打印保存消息
        """
        @self.bot.register(except_self=False)
        def print_all_messages(msg):
            if self.SysType == "win32":
                if savedb:
                    print("\n[{} \033[1;31m接收所有消息(DB) ↙\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
                else:
                    print("\n[{} \033[1;31m接收所有消息 ↙\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            else:
                if savedb:
                    print("\n[{} \033[1;31m接收所有消息(DB) ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
                else:
                    print("\n[{} \033[1;31m接收所有消息 ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            if savedb:
                #将消息保存到mongodb
                if infomsg:
                    print("保存消息到mongodb!!!")

                if "Group" not in str(msg.sender):
                    senders = self.get_user(str(msg.sender))
                else:
                    senders = self.get_user(str(msg.sender)) + ">" + self.get_user(str(msg.member))

                receivers = self.get_user(str(msg.receiver))
                msgtype = msg.type

                #判断消息类型
                if msg.type in self.msgtypelist:               
                    saveurl = self.Save_medis_all(msg, True)
                    msg_content = {
                        '消息类型': msgtype,
                        '访问资源的URL': saveurl
                    }
    
                    insert_content = {
                            '消息发送时间': msg.create_time,
                            '消息接收时间': msg.receive_time,
                            '消息发送者': senders,
                            '消息接收者': receivers,
                            '消息内容': msg_content
                        }
                    if infomsg:
                        print("需要插入的内容为：", insert_content)

                    s = threading.Thread(target=self.save_to_mongodb, args=(insert_content, savedb, infomsg,))
                    s.start()

                    #保存文件
                    saveurl = threading.Thread(target=self.Save_medis_all, args=(msg,))
                    saveurl.start()
                else:
                    if msg.url:
                        msg_content = {
                        '消息类型': msgtype,
                        '文本内容': msg.text,
                        '消息URL': msg.url
                        }
    
                        insert_content = {
                            '消息发送时间': msg.create_time,
                            '消息接收时间': msg.receive_time,
                            '消息发送者': senders,
                            '消息接收者': receivers,
                            '消息内容': msg_content
                        }
                    else: 
    
                        msg_content = {
                        '消息类型': msgtype,
                        '文本内容': msg.text
                        }

                        insert_content = {
                            '消息发送时间': msg.create_time,
                            '消息接收时间': msg.receive_time,
                            '消息发送者': senders,
                            '消息接收者': receivers,
                            '消息内容': msg_content
                        }
                    if infomsg:
                        print("需要插入的内容为：", insert_content)

                    s = threading.Thread(target=self.save_to_mongodb, args=(insert_content, savedb, infomsg,))
                    s.start()

        self.bot.join()

    def Receive_one(self, my_obj):
        @self.bot.register(my_obj, except_self=False)
        def print_one_messages(msg):
            print(msg)


    def get_datetime(self):
        now = datetime.datetime.now()
        nowtime = now.strftime('%Y-%m-%d %H:%M:%S')
        return nowtime

    def get_func_who(self, userinput):
        if userinput not in self.friendslist and userinput not in self.groupslist:
            print("您输入的好友或者群聊不存在，请重新输入!")
        elif userinput in self.friendslist:
            my_friend = self.bot.friends().search(userinput)[0]
            return my_friend
        elif userinput in self.groupslist:
            my_group = self.bot.groups().search(userinput)[0]
            return my_group
        elif userinput == self.console:
            self.get_who_msg()


    #获取好友或群聊对象，可以通过接口，也可以通过终端
    def get_who_msg(self):   
        while True:
            datetimeinfo = self.get_datetime()
            inputflag = datetimeinfo + " {}".format(self.myself)
            user_input = prompt('[{}{}]: '.format(inputflag, "@InputUser"),
                    history=FileHistory('history.txt'),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.NameCompleter,
                    )
            #判断用户输入
            if user_input == "":
                continue
            elif user_input not in self.friendslist and user_input not in self.groupslist:
                print("您输入的好友或者群里不存在，请重新输入!")
                continue
            elif user_input in self.friendslist:
                print("您输入的用户为: ", user_input)
                my_friend = self.bot.friends().search(user_input)[0]
                return my_friend
                break
            else:
                print("你输入的群聊名称为: ", user_input)
                my_group = self.bot.groups().search(user_input)[0]
                return my_group
                break



    def Save_medis_all(self, msg, geturl=False):
        now = datetime.datetime.now()
        nowtime = now.strftime('%Y%m%d%H%M%S')
        receive_time = msg.receive_time
        msg_sender = re.sub(">", "" ,str(msg.sender).split()[1])
        if str(msg.member) == "None":
            specific_sender = msg_sender
        else:
            specific_sender = re.sub(">", "" ,str(msg.member).split()[1])
        file_name = specific_sender + "-" + msg.file_name
        save_path_name = "media/" + msg_sender
        if not os.path.isdir(save_path_name):
            os.makedirs(save_path_name)
        file_path = save_path_name + "/" + file_name

        if geturl == True:
            saveurl = self.saveurl + msg_sender + "/" + file_name
            return saveurl
        else:
            msg.get_file(save_path=file_path)



    def Print_help(self):
        help_info = """
        h|help)     打印帮助信息!             auto)        开启自动聊天功能
        u)          切换会话用户！            all)         打印所有聊天信息！
        q|exit)     退出当前程序！
         """
        print(help_info)



    def Console(self):
        #建立用户对象
        my_obj = self.get_who_msg()

        while True:
            datetimeinfo = self.get_datetime()
            inputflag = datetimeinfo + " {}".format(self.myself)
            console_input = prompt('[{}{}]: '.format(inputflag, "@Console"),
                    history=FileHistory('history.txt'),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.NameCompleter,
                    )
            if console_input == "":
                continue
            elif console_input == "h" or console_input == "help":
                self.Print_help()
                continue
            elif console_input == "all":
                print("\nAll messages are about to start receiving !!! ↩\n")
                all = threading.Thread(target=self.Receive_All, args=())
                all.start()
                continue
            elif console_input == "auto":
                print("开启自动聊天功能！")
                r = threading.Thread(target=self.Receive_Relpy_Msg, args=(my_obj,))
                r.start()
                continue
            elif console_input == "u":
                my_obj = self.get_who_msg()
                continue
            elif console_input == "q" or console_input == "exit":
                sys.exit(0)
            elif console_input == "myrobot":
                print("开启我的自动聊天功能！")
                r = threading.Thread(target=self.Receive_Relpy_My_Msg, args=(my_obj,))
                r.start()
            continue
