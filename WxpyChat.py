#!/data/software/python3.7/bin/python3
# -*- coding: UTF-8 -*-

import re
import sys
import time
import datetime
import threading
from wxpy import *
from prompt_toolkit import prompt
from prettytable import PrettyTable
from colorama import init, Fore, Back, Style
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion.word_completer import WordCompleter



class ConsoleWx(object):

    def __init__(self):
        #判断运行平台
        info = """当前运行平台为 Linux. 请将此二维码全部复制到windowns平台上的编辑器打开，用手机微信扫码登录!若已经登录，请忽略！
        (注：白色背景色的编辑器请将console_qr的值设置为-2，非白背景色的设置为2)
        """
        SysType = sys.platform
        if SysType == "linux":
            print(info)
            bot = Bot(console_qr=2,cache_path=True)
        else:
            SysType = "Windows"
            bot = Bot(cache_path=True)

        #基本设置
        bot.messages.max_history = 10000

        #获取登录名
        myself = re.sub(">", "", str(bot.self).split()[1])
        #初始化表格
        table = PrettyTable(["说明","当前登录用户名", "当前登登陆平台", "好友数量", "帮助信息"])

        # 获取所有好友和群组
        allfriends = bot.friends()
        allgroup = bot.groups()
        friendslist = []
        groupslist = []
        who = ""

        #所有朋友
        for i in allfriends:
            name = re.sub(">", "", str(i).split()[1])
            friendslist.append(name)

        #所有群聊
        for g in allgroup:
            groupname = re.sub(">", "", str(g).split()[1])
            groupslist.append(groupname)

        #添加表格数据
        table.align["登录名"] = "1"
        table.padding_width = 2
        table.add_row(["欢迎使用微信终端聊天小工具", myself, SysType, len(friendslist), "进入用户会话后 输入 h 或 help 查看帮助信息"])
        print(table)

        # 合并 friendslist + groupslist
        FriendsGroupList = friendslist + groupslist

        #构造自动补全的数据
        NameCompleter = WordCompleter(FriendsGroupList, ignore_case=True)


        #初始化数据
        self.NameCompleter = NameCompleter
        self.friendslist = friendslist
        self.groupslist = groupslist
        self.myself = myself
        self.bot = bot


    def getfriends(self, who):
        # 获取指定好友
        my_friends = self.bot.friends().search(who)[0]
        friendsname = re.sub(">", "", str(my_friends).split()[1])
        return my_friends

    def getgroup(self, groupname):
        # 获取指定群聊
        my_group = self.bot.groups().search(groupname)[0]
        groupname = re.sub(">", "", str(my_group).split()[1])
        return my_group


    def Get_who_msg(self):
        while True:
            print("您想与谁建立会话关系呢？\n")
            who = prompt('[请输入建立会话的用户名(注: 按tab键可自动补全用户名)]: ', history=FileHistory('who.txt'),
                        auto_suggest=AutoSuggestFromHistory(),
                        completer=self.NameCompleter,
                        )
            if who == "":
                print("输入用户不能为空!!! 请重新输入。\n")
                continue
            elif who not in self.friendslist and who not in self.groupslist:
                print("您输入的用户名或群聊名称不存在，请您检查后重新输入！")
                continue
            elif who in self.friendslist:
                print("\n与[{}] <好友>建立会话成功.[OK] 可以与好友发送消息.\n".format(who))
                break
            else:
                print("\n与[{}] <群聊>建立会话成功.[OK] 可以在群聊中发送消息.\n".format(who))
                break
        return who


    def Receive_one(self, who, datatime,):
        Who = who
        @self.bot.register(Who, except_self=False)
        def print_one_messages(msg):
            print("\n[{} {}@{} ↩ ]".format(datatime, Who, self.myself), msg)
        self.bot.join()


    def Receive_All(self):
        @self.bot.register(except_self=False)
        def print_all_messages(msg):
            print("\n[接收所有消息 ↩ ]", msg)
        self.bot.join()


    def Print_help(self):
        help_info = """
        h|help)     打印帮助信息!         g)           列出所有群聊！
        u)          切换会话用户！        all)         打印所有聊天信息！
        l)          列出用户列表！        close)       关闭打印所有聊天信息！
        q)          退出！               
        """
        print(help_info)

    def SendRecv(self, who, nowtime, user_input):
        if who in self.friendslist:
            my_friends = self.getfriends(who)
            r = threading.Thread(target=self.Receive_one, args=(my_friends,nowtime,))
            #r.setDaemon(True)
            r.start()
        else:
            my_group = self.getgroup(who)
            r = threading.Thread(target=self.Receive_one, args=(my_group,nowtime,))
            #r.setDaemon(True)
            r.start()


    def Send_msg(self):
        #建立对象
        who = self.Get_who_msg()

        while True:
            now = datetime.datetime.now()
            nowtime = now.strftime('%Y-%m-%d %H:%M:%S')
            if who in self.friendslist:
                inputflag = nowtime + " {root}@【{who}】 <好友> #按u可切换用户 ↪".format(root=self.myself, who=who)
            elif who in self.groupslist:
                inputflag = nowtime + " {root}@【{who}】 <群聊> #按u可切换用户 ↪".format(root=self.myself, who=who)

            user_input = prompt('[{}]: '.format(inputflag), history=FileHistory('send.txt'),
                                            auto_suggest=AutoSuggestFromHistory(),
                                           )
            #删除用户输入的空格
            user_input = user_input.strip()
            if user_input == "":
                #print("不能发送空白消息!!!请重新输入消息内容.\n")
                continue
            elif user_input == "h" or user_input == "help":
                self.Print_help()
            elif user_input == "u":
                #self.bot.registered.enable(self.print_one_messages)
                who = self.Get_who_msg()
                self.SendRecv(who, nowtime, user_input)
                continue
            elif user_input == "l":
                print(self.friendslist)
                continue
            elif user_input == "g":
                print(self.groupslist)
                continue
            elif user_input == "all":
                print("\nOutput all messages to the terminal !!! ↩\n")
                all = threading.Thread(target=self.Receive_All, args=())
                all.start()
                #self.bot.registered.enable(self.print_all_messages)
                continue
            elif user_input == "close":
                #self.bot.registered.disable(self.print_all_messages)
                print("功能正在开发中......")
                continue
            elif user_input == "q":
                print("Logout Success!")
                self.bot.logout
                exit(0)
            else:
                if who in self.friendslist:
                    my_friends = self.getfriends(who)
                    r = threading.Thread(target=self.Receive_one, args=(my_friends,nowtime,))
                    #r.setDaemon(True)
                    r.start()
                    if user_input != "" or user_input != "\n":
                        print("\n↪ {}: {}\n".format(who, user_input))
                    my_friends.send(user_input)
                else:
                    my_group = self.getgroup(who)
                    r = threading.Thread(target=self.Receive_one, args=(my_group,nowtime,))
                    #r.setDaemon(True)
                    r.start()
                    #if "↩"  not in user_input:
                    if user_input != "" or user_input != "\n":
                        print("\n↪ {}: {}\n".format(who, user_input))
                    my_group.send(user_input)
            continue



def main():
    try:
        Mychat = ConsoleWx()
        Mychat.Send_msg()
    except Exception as e:
        exit(e)


if __name__ == '__main__':
    main()
        
