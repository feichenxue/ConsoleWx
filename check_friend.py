#!/data/software/python3.7/bin/python3
# -*- coding: UTF-8 -*-

import time
import sys
from wxpy import *

bot = Bot(console_qr=2,cache_path=True)

my_friend=bot.friends()

embed()

for i in range(1,len(my_friend)):
    time.sleep(2)#延时根据检测频率限制而定
    print('-----[%s] %d/%d-------'%(my_friend[i], i, len(my_friend)))
    print("周末愉快[微笑]")
    #my_friend[i].send_msg("周末愉快[呲牙]")
