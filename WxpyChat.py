#!/data/software/python3.7/bin/python3
# -*- coding: UTF-8 -*-

import re
import os
import sys
import time
import signal
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
        #初始化颜色
        SysType = sys.platform
        if SysType == "linux":
            print(Fore.RED + info)
            print(Style.RESET_ALL)
            bot = Bot(console_qr=2,cache_path=True)
        else:
            SysType = "win32"
            bot = Bot(cache_path=True)

        #基本设置
        bot.messages.max_history = 10000
        bot.auto_mark_as_read = True

        #获取登录名
        myself = re.sub(">", "", str(bot.self).split()[1])
        #初始化表格
        table = PrettyTable(["说明","当前登录用户名", "当前登登陆平台", "好友数量", "帮助信息"])

        # 获取所有好友和群组
        allfriends = bot.friends()
        allgroup = bot.groups()
        friendslist = []
        groupslist = []
        GList = []
        Mplist = []
        who = ""

        #所有好友和群聊和公众号
        ALLChats = bot.chats()
        for all in ALLChats:
            tmp = re.sub(">", "", str(all).split()[1])
            if "Group" in str(all).split()[0]:
                GList.append(tmp)
            elif "MP" in str(all).split()[0]:
                Mplist.append(tmp)


        #所有朋友
        for i in allfriends:
            name = re.sub(">", "", str(i).split()[1])
            friendslist.append(name)

        #所有群聊
        for g in allgroup:
            groupname = re.sub(">", "", str(g).split()[1])
            groupslist.append(groupname)


        #添加表格数据
        if SysType == "win32":
            ShowsysType = "Windows"
        table.align["登录名"] = "1"
        table.padding_width = 2
        table.add_row(["欢迎使用微信终端聊天小工具", myself, ShowsysType, len(friendslist), "进入用户会话后 输入 h 或 help 查看帮助信息"])
        print(table)

        # 合并 friendslist + groupslist
        FriendsGroupList = friendslist + GList

        #构造自动补全的数据
        NameCompleter = WordCompleter(FriendsGroupList, ignore_case=True)
        Emoticon = WordCompleter(['[捂脸]','[微笑]', '[撇嘴]', '[色]', '[发呆]', '[得意]', '[大哭]', '[尴尬]', '[发怒]', '[调皮]', '[呲牙]',
            '[吐]', '[偷笑]', '[愉快]', '[白眼]', '[傲慢]', '[流泪]', '[惊讶]', '[困]', '[害羞]', '[难过]', '[惊恐]', '[闭嘴]', '[囧]', '[流汗]',
            '[睡]', '[抓狂]', '[憨笑]', '[敲打]', '[鄙视]', '[悠闲]', '[再见]', '[委屈]', '[奋斗]', '[擦汗]', '[快哭了]', '[咒骂]', '[抠鼻]', '[阴脸]', 
            '[疑问]', '[鼓掌]', '[亲亲]', '[嘘]', '[坏笑]', '[可怜]', '[晕]', '[左哼哼]', '[右哼哼]', '[菜刀]', '[衰]', '[西瓜]', '[骷髅]', '[哈欠]', 
            '[啤酒]', '[炸弹]', '[抱拳]', '[咖啡]', '[便便]', '[勾引]', '[猪头]', '[月亮]', '[拳头]', '[玫瑰]', '[太阳]', '[OK]', '[凋谢]', '[拥抱]', 
            '[跳跳]', '[嘴唇]', '[强]', '[发抖]', '[爱心]', '[弱]', '[怄火]', '[心碎]', '[握手]', '[转圈]', '[蛋糕]', '[胜利]', '[笑脸]', '[礼物]',
            '[生病]', '[奸笑]', '[红包]', '[破涕为笑]', '[机智]', '[發]', '[吐舌]', '[皱眉]', '[福]', '[脸红]', '[耶]', '[恐惧]', '[鬼魂]', '[失望]',
            '[合十]', '[无语]', '[强壮]', '[嘿哈]'])


        #初始化数据
        self.NameCompleter = NameCompleter
        self.Emoticon = Emoticon
        self.friendslist = friendslist #所有朋友
        self.groupslist = groupslist    #仅仅保存到通讯录得群聊
        self.GList = GList              #所有群聊
        self.ALLChatsList = FriendsGroupList  #所有好友和群聊列表
        self.Mplist = Mplist  #关注的微信公众号
        self.myself = myself
        self.bot = bot
        self.SysType = SysType

    def get_datetime(self):
        now = datetime.datetime.now()
        nowtime = now.strftime('%Y-%m-%d %H:%M:%S')
        return nowtime


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
            print(Fore.MAGENTA + "您想与谁建立会话关系呢？\n", Style.RESET_ALL)
            who = prompt('[请输入建立会话的用户名(注: 按tab键可自动补全用户名)]: ', history=FileHistory('who.txt'),
                        auto_suggest=AutoSuggestFromHistory(),
                        completer=self.NameCompleter,
                        )
            if who == "":
                inputinfo = """
        输入用户不能为空, 请重新输入!!!
        请输入 l 或 g 列出当前用户 和 群聊[只显示当前活跃群且保存到通讯录的群聊]。
        输入 G 显示 所有群聊。
        输入 all 显示所有群聊和好友信息。
        """
                print("\n %s \n" % (inputinfo))
                continue
            elif who == "l":
                print(self.friendslist)
                continue
            elif who == "g":
                print(self.groupslist)
                continue
            elif who == "G":
                print(self.GList)
                continue
            elif who == "all":
                print(self.ALLChatsList)
                continue
            elif who not in self.friendslist and who not in self.groupslist:
                print("您输入的用户名或群聊名称不存在，请您检查后重新输入！")
                continue
            elif who in self.friendslist:
                print("\n与[{}] <好友>建立会话成功.[OK] 可以与好友发送消息.\n".format(who))
                nowtime = self.get_datetime
                r= threading.Thread(target=self.Receive_one, args=(who, nowtime,))
                r.start()
                break
            else:
                print("\n与[{}] <群聊>建立会话成功.[OK] 可以在群聊中发送消息.\n".format(who))
                nowtime = self.get_datetime
                r= threading.Thread(target=self.Receive_one, args=(who, nowtime,))
                r.start()
                break
        return who


    def Save_medis_one(self, msg, who):
        now = datetime.datetime.now()
        nowtime = now.strftime('%Y%m%d%H%M%S')
        receive_time = msg.receive_time
        msg_sender = who
        if str(msg.member) == "None":
            specific_sender = msg_sender
        else:
            specific_sender = re.sub(">", "" ,str(msg.member).split()[1])
        file_name = specific_sender + "-" + msg.file_name
        save_path_name = "media/" + msg_sender
        if not os.path.isdir(save_path_name):
            os.makedirs(save_path_name)
        file_path = save_path_name + "/" + file_name
        msg.get_file(save_path=file_path)


    def Save_medis_all(self, msg):
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
        msg.get_file(save_path=file_path)
        return receive_time



    def Receive_one(self, who, datatime):
        # rLock = threading.RLock()  #RLock对象
        if len(str(who).split()) > 1:
            Who = re.sub(">", "", str(who).split()[1])
        else:
            Who = str(who).split()[0]

        @self.bot.register(who, except_self=False)
        def print_one_messages(msg):
            if Who in self.friendslist:
                if self.SysType == "win32":
                    print("\n[{} 【{}】@{} <好友> (\033[1;31m接收\033[0m) ↙]: ".format(datatime, Who, self.myself), "\033[0;32m{}\033[0m".format(msg))
                else:
                    print("\n[{} 【{}】@{} <好友> (\033[1;31m接收\033[0m) ↩]: ".format(datatime, Who, self.myself), "\033[0;32m{}\033[0m".format(msg))
            else:
                if self.SysType == "win32":
                    print("\n[{} 【{}】@{} <群聊> (\033[1;31m接收\033[0m)↙]: ".format(datatime, Who, self.myself), "\033[0;32m{}\033[0m".format(msg))
                else:
                    print("\n[{} 【{}】@{} <群聊> (\033[1;31m接收\033[0m)↩]: ".format(datatime, Who, self.myself), "\033[0;32m{}\033[0m".format(msg))
            self.Save_medis_one(msg, Who)
            # rLock.release()
        self.bot.join()


    def Receive_All(self):
        rLock = threading.RLock()
        @self.bot.register(except_self=False)
        def print_all_messages(msg):
            rLock.acquire()
            msgtypelist = ["Picture","Recording","Attachment","Video"]
            print("\n[{} \033[1;31m接收所有消息 ↩\033[0m]".format(msg.receive_time), "\033[0;32m{}\033[0m".format(msg))
            if msg.type in msgtypelist:
                datatime = self.Save_medis_all(msg)
            rLock.release()
        self.bot.join()


    def Print_help(self):
        help_info = """
        h|help)     打印帮助信息!             g)           列出所有群聊（注：仅仅显示保存到通讯录的群聊)!
        u)          切换会话用户！            all)         打印所有聊天信息！
        l)          列出用户列表！            close)       关闭打印所有聊天信息！
        q)          退出！                   lg)           列出所有群聊和好友！
        m)          打印所有关注的公众号！
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

    def Print_all_msg(self):
        all = threading.Thread(target=self.Receive_All, args=())
        all.start()


    def Send_msg(self):
        #建立对象
        who = self.Get_who_msg()

        while True:
            now = datetime.datetime.now()
            nowtime = now.strftime('%Y-%m-%d %H:%M:%S')
            if who in self.friendslist:
                if self.SysType == "win32":
                    inputflag = nowtime + " {root}@【{who}】 <好友> (发送)→".format(root=self.myself, who=who)
                else:
                    inputflag = nowtime + " {root}@【{who}】 <好友> (发送)↪".format(root=self.myself, who=who)
            elif who in self.groupslist:
                if self.SysType == "win32":
                    inputflag = nowtime + " {root}@【{who}】 <群聊> (发送)→".format(root=self.myself, who=who)
                else:
                    inputflag = nowtime + " {root}@【{who}】 <群聊> (发送)↪".format(root=self.myself, who=who)
            user_input = prompt('[{}]: '.format(inputflag), history=FileHistory('send.txt'),
                                            auto_suggest=AutoSuggestFromHistory(),
                                            completer=self.Emoticon,
                                           )
            #删除用户输入的空格
            user_input = user_input.strip()
            if user_input == "":
                #print("不能发送空白消息!!!请重新输入消息内容.\n")
                continue
            elif user_input == "h" or user_input == "help":
                self.Print_help()
                continue
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
            elif user_input == "lg":
                print(self.ALLChatsList)
                continue
            elif user_input == "m":
                print(self.Mplist)
                continue
            elif user_input == "all":
                if self.SysType == "win32":
                    print("\nAll messages are about to start receiving !!!↙\n")
                else:
                    print("\nAll messages are about to start receiving !!!↩\n")
                self.Print_all_msg()
                #self.bot.registered.enable(self.print_all_messages)
                continue
            elif user_input == "close":
                #self.bot.registered.disable(self.print_all_messages)
                print("功能正在开发中......")
                continue
            elif user_input == "q":
                self.bot.logout
                print("Exit Success!")
                os.kill(os.getpid(), signal.SIGKILL)
            else:
                if who in self.friendslist:
                    my_friends = self.getfriends(who)
                    r = threading.Thread(target=self.Receive_one, args=(my_friends,nowtime,))
                    #r.setDaemon(True)
                    r.start()
                    if user_input != "" or user_input != "\n":
                        # print("\n↪ {}: {}\n".format(who, user_input))
                        print("\033[0;32mSend Successfully!!!\033[0m")
                    my_friends.send(user_input)
                else:
                    my_group = self.getgroup(who)
                    r = threading.Thread(target=self.Receive_one, args=(my_group,nowtime,))
                    #r.setDaemon(True)
                    r.start()
                    #if "↩"  not in user_input:
                    if user_input != "" or user_input != "\n":
                        # print("\n↪ {}: {}\n".format(who, user_input))
                        print("\033[0;32mSend Successfully!!!\033[0m")
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
