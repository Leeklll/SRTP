import subprocess, sqlite3, re
import os
import sys
import math
import time

#获取当前日期
year=time.strftime('%Y')
month=time.strftime('%m')
day=time.strftime('%d')

#将一定格式的日期时间字符串转换为Unix timestamp
def dt_stamp(year, month, day, hour, minute, second):
	datetime=year+'-'+month+'-'+day+' '+hour+':'+minute+':'+second
	timestamp=int(time.mktime(time.strptime(datetime, '%Y-%m-%d %H:%M:%S')))
	return timestamp
def lshw():
#func:用于查找字符串A分割后的表中字符串B后面一项字符串C，存在表list_C中
  def split_after(A,B):
	  last=''
	  list_C=[]
	  strsplit=A.split()
	  for piece in strsplit:
		  if last==B:
			  list_C.append(piece)
		  last=piece
	  return list_C

#初始化可能因采集不到而出错的目标数据为-1
  cpu_capacity='-1'
  width='-1'
  cores='-1'
  enabledcores='-1'
  threads='-1'
  network_capacity='-1'
  
#------------------------------------CPU----------------------------------
#lshw -C cpu
  lshw_cpu_info=subprocess.Popen('lshw -C cpu', shell=True, stdout=subprocess.PIPE)
  out0, err0=lshw_cpu_info.communicate()
  lshw_cpu_str=out0.decode(encoding='utf-8', errors='ignore')

#capacity(cpu)
  cpu_capacity_str_list=split_after(lshw_cpu_str, 'capacity:')
  for cpu_capacity_str in cpu_capacity_str_list:
	  cpu_capacity=cpu_capacity_str[:-3]

#width
  width_str_list=split_after(lshw_cpu_str, 'width:')
  for width_str in width_str_list:
	   width=width_str

#cores, enabledcores, threads
  cpu_str_list=lshw_cpu_str.split()#全部分割
  for string in cpu_str_list:
	  if string[0:6]=='cores=':
		  cores_str=string[6:]
		  cores=cores_str
	  if string[0:13]=='enabledcores=':
		  enabledcores_str=string[13:]
		  enabledcores=enabledcores_str
	  if string[0:8]=='threads=':
		  threads_str=string[8:]
		  threads=threads_str
		  
#------------------------------------memory-------------------------------
#lshw -C memory
  lshw_memory_info=subprocess.Popen('lshw -C memory', shell=True, stdout=subprocess.PIPE)
  out1, err1=lshw_memory_info.communicate()
  lshw_memory_str=out1.decode(encoding='utf-8', errors='ignore')

#cache size, slot
  memory_str_list=lshw_memory_str.split('*')#根据“*”将字段分开
  cache_size_list=[]
  cache_slot_list=[]
  for memory_str in memory_str_list:
	  if memory_str[0:7]=='-cache:':
		  size_list=split_after(memory_str, 'size:')
		  if size_list:
			  cache_size_list.append(size_list[0])
		  slot_list=split_after(memory_str, 'slot:')
		  if slot_list:
			  cache_slot_list.append(slot_list[0])

#memory count
  memory_count_num=len(re.findall('\*-bank', lshw_memory_str))#对*-bank进行计数
  memory_count=str(memory_count_num)

#memory size
  memory_size_list=[]
  for memory_str in memory_str_list:
	  if memory_str[0:7]=='-memory':
		  msize_list=split_after(memory_str, 'size:')
		  if msize_list:
			  memory_size_list.append(msize_list[0])
  memory_size=memory_size_list[0]

#------------------------------------disk---------------------------------
#lshw -C disk
  lshw_disk_info=subprocess.Popen('lshw -C disk', shell=True, stdout=subprocess.PIPE)
  out2, err2=lshw_disk_info.communicate()
  lshw_disk_str=out2.decode(encoding='utf-8', errors='ignore')

#disk count
  disk_count_num=len(re.findall('\*-disk', lshw_disk_str))#对*-disk进行计数
  disk_count=str(disk_count_num)

#logic name(disk) size(disk)
  disk_str_list=lshw_disk_str.split('*')#根据“*”将字符串分割，便于提取disk有关项
  disk_logic_name_list=[]
  disk_size_list=[]
#在*-disk的字段中查找logic name和size
  for disk_str in disk_str_list:
	  if disk_str[0:5]=='-disk':
		  name_list=split_after(disk_str, 'name:')
		  if name_list:
			  disk_logic_name_list.append(name_list[0])
		  size_list=split_after(disk_str, 'size:')
		  if size_list:
			  disk_size_list.append(size_list[0])

#type (1 for HDD, 0 for SSD)
  lsblk_info=subprocess.Popen('lsblk -d -o name,rota', shell=True, stdout=subprocess.PIPE)
  out4, err4=lsblk_info.communicate()
  lsblk_str=out4.decode(encoding='utf-8', errors='ignore')

  t_list=lsblk_str.split()
  t_list=t_list[2:]#除去name和rota
  i=1
  namelist=[]
  rotalist=[]
  for t in t_list:
	  if i%2==1:
		  namelist.append(t)
		  i+=1
	  else:
		  rotalist.append(t)
		  i+=1
  disk_type_list=[]#type与logic name list中的各项相对应
  i=0
  for disk_logic_name in disk_logic_name_list:
	  for name in namelist:
		  if re.search(name, disk_logic_name):
			  disk_type_list.append(namelist[i]+'---'+rotalist[i])
		  i+=1
	  i=0

#-------------------------------------network-------------------------------
#lshw -C network
  lshw_network_info=subprocess.Popen('lshw -C network', shell=True, stdout=subprocess.PIPE)
  out3, err3=lshw_network_info.communicate()
  lshw_network_str=out3.decode(encoding='utf-8', errors='ignore')

#network count
  network_count_num=len(re.findall('clock:', lshw_network_str))
  network_count=str(network_count_num)

#logic name(network)
  network_logic_name_list=split_after(lshw_network_str, 'name:')

#capacity(network)
  network_capacity_list=split_after(lshw_network_str, 'capacity:')
  network_capacity=network_capacity_list[0]

#-------------------------------------SQLite3-------------------------------
  print('\n\n________SQLite3________')

  getRC=lambda cur: cur.rowcount if hasattr(cur, 'rowcount') else -1
  conn=sqlite3.connect('static_metrics.db')
  try:
	  curs=conn.cursor()
	  curs.execute('CREATE TABLE STATIC_METRICS (name TEXT, data BLOB)')
  except Exception:print('Create Table:STATIC_METRICS Successfully!')
  finally:
	#write
	##CPU
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('CPU_capacity', '%s')"%cpu_capacity)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('CPU_width', '%s')"%width)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('CPU_cores', '%s')"%cores)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('CPU_enabledcores', '%s')"%enabledcores)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('CPU_threads', '%s')"%threads)
	##MEMORY	
	  for cache_size in cache_size_list:	
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('MEMORY_cache size', '%s')"%cache_size)
	  for cache_slot in cache_slot_list:	
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('MEMORY_cache slot', '%s')"%cache_slot)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('MEMORY_count', '%s')"%memory_count)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('MEMORY_size', '%s')"%memory_size)
	##DISK
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('DISK_count', '%s')"%disk_count)
	  for disk_logic_name in disk_logic_name_list:
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('DISK_logic name', '%s')"%disk_logic_name)
	  for disk_size in disk_size_list:
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('DISK_size', '%s')"%disk_size)
	  for disk_type in disk_type_list:
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('DISK_type', '%s')"%disk_type)
	##NETWORK
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('NETWORK_count', '%s')"%network_count)
	  for network_logic_name in network_logic_name_list:
		  curs.execute("INSERT INTO STATIC_METRICS VALUES('NETWORK_logic name', '%s')"%network_logic_name)
	  curs.execute("INSERT INTO STATIC_METRICS VALUES('NETWORK_capacity', '%s')"%network_capacity)
	  conn.commit()

	#read
#	  curs.execute('SELECT * FROM STATIC_METRICS')
#	  for row in curs.fetchall():
#		  print(row[0], row[1])

	  #output=open('/home/leepech/temp/static_metrics.txt', 'w')
	  #print('open file\n')
	  #output.write('METRIC\t INFO\n')#表头  
	  exDb_st_mtr()
	  
	  curs.close()
	  conn.close()


#lpc2020
##########################################################################
##########################################################################

#CPU
def sar():
 
#for i in range(0,lines):
#     count=len(sar_cpu_str[i].split('     '))
#     sar_cpu_str[i]=sar_cpu_str[i].split('     ')
#sar_cpu_str=sar_cpu_str.split('     ')
#print(lines)
#print(count)
#print(sar_cpu_str)
  
   #curs.execute('CREATE TABLE mhz(id INTEGER,eleven TEXT,Mhz float)')      
#-------------------------------cpu------------------------------------------
  sar_cpu_info=subprocess.Popen('sar -u ALL -P ALL 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_cpu_info.communicate()
  sar_cpu_str=out0.decode(encoding='utf-8', errors='ignore')
  lines=len(sar_cpu_str.split('\n'))
  sar_cpu_str=sar_cpu_str.split('\n')#分割字符
#mhz
  sar_mhz_info=subprocess.Popen('sar -m CPU -P ALL 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_mhz_info.communicate()
  sar_mhz_str=out0.decode(encoding='utf-8', errors='ignore')
  lines_mhz=len(sar_mhz_str.split('\n'))
  sar_mhz_str=sar_mhz_str.split('\n')#分割字符
  
#curs.execute("INSERT INTO mhz VALUES(11,'cpu MHz:',%f)"%mhz[7][2])
  #------Memory:   sar -r ALL   
  sar_r_info=subprocess.Popen('sar -r ALL 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_r_info.communicate()
  sar_r_str=out0.decode(encoding='utf-8', errors='ignore')

  lines_r=len(sar_r_str.split('\n'))
  sar_r_str=sar_r_str.split('\n')


#------Memory:   sar -B------------------------------
  sar_B_info=subprocess.Popen('sar -B 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_B_info.communicate()
  sar_B_str=out0.decode(encoding='utf-8', errors='ignore')

  lines_B=len(sar_B_str.split('\n'))
  sar_B_str=sar_B_str.split('\n')
  
#-----------------------disk: ------------------------
  disk_info = subprocess.Popen(['sar',  '-d', '1', '1'], stdout=subprocess.PIPE)
  out, err = disk_info.communicate() 
  sar_disk=out.decode(encoding='utf-8', errors='ignore')#获取disk的值
  sardisk=sar_disk.split()#将所获取的字符串按照空格逐个分割
  i=sardisk.index('%util')#获取头部的位置
  i=i+1
  tail=sardisk.index("平均时间:")#获取尾部的位置
  disk_row=(tail-i)/10
  disk_row=int(disk_row)#获取数据行数
  disk_time=[]#初始化所要获取的数据列表
  disk_dev=[]
  disk_tps=[]
  disk_rkbs=[]
  disk_wkbs=[]
  disk_areq=[]
  disk_aqu=[]
  disk_await=[]
  disk_svctm=[]
  disk_util=[]
  for n in range(0,disk_row):
   time_str=sardisk[i]
   #时间字符串的格式固定，直接按位分割
   h_str=time_str[0:2]
   m_str=time_str[3:5]
   s_str=time_str[6:8]
   #unix timestamp
   disk_time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
   disk_time.append(disk_time_stamp)
   i+=1
   disk_dev.append(sardisk[i])
   i+=1
   disk_tps.append(float(sardisk[i]))
   i+=1
   disk_rkbs.append(float(sardisk[i]))
   i+=1
   disk_wkbs.append(float(sardisk[i]))
   i+=1
   disk_areq.append(float(sardisk[i]))
   i+=1
   disk_aqu.append(float(sardisk[i]))
   i+=1
   disk_await.append(float(sardisk[i]))
   i+=1
   disk_svctm.append(float(sardisk[i]))
   i+=1
   disk_util.append(float(sardisk[i]))
   i+=1
#-------------------------任务创建与系统转换统计信息--------------------------------
  task_info = subprocess.Popen(['sar',  '-w', '1', '1'], stdout=subprocess.PIPE)
  out, err = task_info.communicate() 
  sar_task=out.decode(encoding='utf-8', errors='ignore')#获取task的值
  sartask=sar_task.split()
  task_time=[]
  task_procs=[]
  task_cswchs=[]
  i=sartask.index('cswch/s')
  i+=1
  tail=sartask.index("平均时间:")#获取尾部的位置
  task_row=(tail-i)/3
  task_row=int(task_row)#获取数据行数
  for n in range(0,task_row):
   time_str=sartask[i]
   h_str=time_str[0:2]
   m_str=time_str[3:5]
   s_str=time_str[6:8]
   #unix timestamp
   task_time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
   task_time.append(task_time_stamp)
   i+=1
   task_procs.append(float(sartask[i]))
   i+=1
   task_cswchs.append(float(sartask[i]))
   i+=1
#------------------I/O和传输速率信息---------------------------------
  io_info = subprocess.Popen(['sar',  '-b', '1', '1'], stdout=subprocess.PIPE)
  out, err = io_info.communicate() 
  sar_io=out.decode(encoding='utf-8', errors='ignore')#获取io的值
  sario=sar_io.split()
  i=sario.index('bwrtn/s')
  i+=1
  tail=sario.index("平均时间:")#获取尾部的位置
  io_row=(tail-i)/6
  io_row=int(io_row)#获取数据行数
  io_time=[]
  io_tps=[]
  io_rtps=[]
  io_wtps=[]
  io_breads=[]
  io_bwrtns=[]
  for n in range(0,io_row):
   time_str=sario[i]
   h_str=time_str[0:2]
   m_str=time_str[3:5]
   s_str=time_str[6:8]
   #unix timestamp
   io_time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
   io_time.append(io_time_stamp)
   i+=1
   io_tps.append(float(sario[i]))
   i+=1
   io_rtps.append(float(sario[i]))
   i+=1
   io_wtps.append(float(sario[i]))
   i+=1
   io_breads.append(float(sario[i]))
   i+=1
   io_bwrtns.append(float(sario[i]))
   i+=1
#-----------------------------系统交换信息---------------------------------------------
  change_info = subprocess.Popen(['sar',  '-W', '1', '1'], stdout=subprocess.PIPE)
  out, err = change_info.communicate() 
  sar_change=out.decode(encoding='utf-8', errors='ignore')#获取change的值
  sarchange=sar_change.split()
  i=sarchange.index('pswpout/s')
  i+=1
  tail=sarchange.index("平均时间:")#获取尾部的位置
  change_row=(tail-i)/3
  change_row=int(change_row)#获取数据行数
  change_time=[]
  change_pswpins=[]
  change_pswpouts=[]
  for n in range(0,change_row):
       time_str=sarchange[i]
       h_str=time_str[0:2]
       m_str=time_str[3:5]
       s_str=time_str[6:8]
 	  #unix timestamp
       change_time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
       change_time.append(change_time_stamp)
       i+=1
       change_pswpins.append(float(sarchange[i]))
       i+=1
       change_pswpouts.append(float(sarchange[i]))
       i+=1
#----------------------------------------NETWORK-----------------------------
  sar_DEV_info=subprocess.Popen('sar -n DEV 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_DEV_info.communicate()
  sar_DEV_str=out0.decode(encoding='utf-8', errors='ignore')
  sar_EDEV_info=subprocess.Popen('sar -n EDEV 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_EDEV_info.communicate()
  sar_EDEV_str=out0.decode(encoding='utf-8', errors='ignore')#解析命令
  lines_DEV=len(sar_DEV_str.split('\n'))
  lines_EDEV=len(sar_EDEV_str.split('\n'))
  sar_DEV_str=sar_DEV_str.split('\n')
  sar_EDEV_str=sar_EDEV_str.split('\n')

  

#------swap:   sar -q-------------------------------
  sar_q_info=subprocess.Popen('sar -q 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_q_info.communicate()
  sar_q_str=out0.decode(encoding='utf-8', errors='ignore')

  lines_q=len(sar_q_str.split('\n'))
  sar_q_str=sar_q_str.split('\n')

#------swap:   sar -S----------------------------------
  sar_S_info=subprocess.Popen('sar -S 1 1', shell=True, stdout=subprocess.PIPE)
  out0, err0=sar_S_info.communicate()
  sar_S_str=out0.decode(encoding='utf-8', errors='ignore')

  lines_S=len(sar_S_str.split('\n'))
  sar_S_str=sar_S_str.split('\n')
#--------------------------------- intr---------------------------------------
  sar_intr_info=subprocess.Popen('sar -I ALL 1 1',shell=True,stdout=subprocess.PIPE)
  out0, err0=sar_intr_info.communicate()
  sar_intr_str=out0.decode(encoding='utf-8', errors='ignore')
  lines_intr=len(sar_intr_str.split('\n'))
  sar_intr_str=sar_intr_str.split('\n')
#--------------------------------database-------------------------------------
  getRC = lambda cur: cur.rowcount if hasattr(cur, 'rowcount') else -1#获取游标所指向是数据的行数

  try:
     conn = sqlite3.connect('somedata.db')                           # 连接数据库
     curs=conn.cursor()                                          # 获取游标
     curs.execute('CREATE TABLE CPU( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,cpu varchar(10),user float,nice float,sys float,idle float, iowait float,irq float, softirq float ,steal float,guest float ,gnice float)')             # 执行代码,创建表和字段# 每次执行完后都应该保存

     curs.execute('CREATE TABLE mhz( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,cpumhz varchar(10),mhz float)') 

     curs.execute('CREATE TABLE memory( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,memused float,commi_t float,kbactive float,kbinac float, kbdirty float, kbanonpg float, kbstack float,kbpgtbl float, kbvmused float )') 

     curs.execute('CREATE TABLE DISK (id INTEGER PRIMARY KEY AUTOINCREMENT, time int, dev varchar(10), tps float,  rkb float,  wkb float, areq float, aqu float,  await float,  svctm float,util float)')
                                           
     curs.execute('CREATE TABLE DEV( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,network varchar(10),rxpck float,txpck float,rxbyt float,txbty float, rxcmp float, txcmp float, rxmcst float,ifutil float)')
     curs.execute('CREATE TABLE EDEV(id INTEGER PRIMARY KEY AUTOINCREMENT,time int,network varchar(10),rxerr float,txerr float,coll float,rxdrop float, txdrop float, txcarr float, rxfram float ,rrxfifo float, txfifo float )')            
                                                              
     curs.execute('CREATE TABLE TASK (id INTEGER PRIMARY KEY AUTOINCREMENT, time int, procs float,  cswchs float)')
     curs.execute('CREATE TABLE IO (id INTEGER PRIMARY KEY AUTOINCREMENT, time int, tps float, rtps float, wtps float, breads float, bwrtns float)')
     curs.execute('CREATE TABLE CHANGE (id INTEGER PRIMARY KEY AUTOINCREMENT, time int,  pswpins float, pswpouts float)')
     curs.execute('CREATE TABLE B( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,pgpgin float,pgpgout float,fault float,majflt float,pgfree float,pgscank float,pgsteal float,vmeff float)')          
      
     curs.execute('CREATE TABLE q( id INTEGER PRIMARY KEY AUTOINCREMENT,time int,runq_sz float,plist_sz float,ldavg_1 float,ldavg_5 float,ldavg_15 float,blocked float )')
     curs.execute('CREATE TABLE S(id INTEGER PRIMARY KEY AUTOINCREMENT,time int,swpused float,swpcad float )')
   #curs.execute('CREATE TABLE mhz(id INTEGER,eleven TEXT,Mhz float)') 
     curs.execute('CREATE TABLE intr(id INTEGER PRIMARY KEY AUTOINCREMENT,time int,sum varchar(10),intr float)')
  except Exception:print(" "); 
#---------------cpu------------------------------------------------ 
  for i in range(0,lines):
       count=len(sar_cpu_str[i].split())
       sar_cpu_str[i]=sar_cpu_str[i].split()
     #print(sar_cpu_str[i])
       for j in range(0,count):
            try:
               if j!=1:
                  sar_cpu_str[i][j]=float(sar_cpu_str[i][j])#转化为浮点数
            except ValueError:
               sar_cpu_str[i][j]=sar_cpu_str[i][j]
       if count==12:
          if sar_cpu_str[i][1]!='CPU':
             if sar_cpu_str[i][0]!='平均时间:':     #剔除不是寻找数据
                time_str=sar_cpu_str[i][0]
                h_str=time_str[0:2]
                m_str=time_str[3:5]
                s_str=time_str[6:8]
		#unix timest
                time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
                curs.execute("INSERT INTO CPU VALUES(NULL,?,?,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f)"%(sar_cpu_str[i][2], sar_cpu_str[i][3], sar_cpu_str[i][4], sar_cpu_str[i][5], sar_cpu_str[i][6], sar_cpu_str[i][7], sar_cpu_str[i][8], sar_cpu_str[i][9], sar_cpu_str[i][10], sar_cpu_str[i][11]),(time_stamp,sar_cpu_str[i][1],)); # 添加记录
  for i in range(0,lines_mhz):
       count=len(sar_mhz_str[i].split())
       sar_mhz_str[i]=sar_mhz_str[i].split()
     #print(sar_cpu_st
       for j in range(0,count):
            try:
               sar_mhz_str[i][j]=float(sar_mhz_str[i][j])#转化为浮点数
            except ValueError:
               sar_mhz_str[i][j]=sar_mhz_str[i][j]
       if count==3:
          if sar_mhz_str[i][0]!='平均时间:':
              if sar_mhz_str[i][1]!='CPU':
                 time_str=sar_mhz_str[i][0]
                 h_str=time_str[0:2]
                 m_str=time_str[3:5]
                 s_str=time_str[6:8]
		  #unix timestamp
                 time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
                    #print(time_stamp,sar_intr_str[i][1])     
                 curs.execute("INSERT INTO mhz VALUES(NULL,?,?,%f)"%(sar_mhz_str[i][2]),(time_stamp,sar_mhz_str[i][1],)); # 添加记录 
#-------------------------------memory-------------------------------
  for i in range(0,lines_r-1):
     count_r=len(sar_r_str[i].split())#获取每行分割数量
     sar_r_str[i]=sar_r_str[i].split()#分割每行
     #print(sar_r_str[i]) 
     #print(count_r)
     if count_r==17:       #判断每行分割数量
        for j in range(0,count_r):
            try:
               sar_r_str[i][j]=float(sar_r_str[i][j])#转化为浮点数

            except ValueError:
               sar_r_str[i][j]=sar_r_str[i][j] 


        if sar_r_str[i][0]!='平均时间:':#判断剔除不是寻找数据
           if sar_r_str[i][1]!='kbmemfree':
              time_str=sar_r_str[i][0]
              h_str=time_str[0:2]
              m_str=time_str[3:5]
              s_str=time_str[6:8]
	      #unix timestam
              time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
              curs.execute("INSERT INTO memory VALUES(NULL,?,%f,%f,%f,%f,%f,%f,%f,%f,%f)"%(sar_r_str[i][3], sar_r_str[i][7], sar_r_str[i][8], sar_r_str[i][9], sar_r_str[i][8], sar_r_str[i][10], sar_r_str[i][12], sar_r_str[i][13], sar_r_str[i][14]),(time_stamp,));
# 添加记录
 
  for i in range(0,lines_B-1):
        count_B=len(sar_B_str[i].split())#获取每行分割数量
      #print(count_B)
      #print(sar_B_str[i])
     
        sar_B_str[i]=sar_B_str[i].split()#分割每行
        if count_B==10:#判断每行分割数量
          for j in range(0,count_B):
              try:
                 sar_B_str[i][j]=float(sar_B_str[i][j])#转化为浮点数
              except ValueError:
                 sar_B_str[i][j]=sar_B_str[i][j] 
           #print(sar_B_str[i][j])
          if sar_B_str[i][0]!='平均时间:':
             if sar_B_str[i][1]!='pgpgin/s':
                time_str=sar_B_str[i][0]
                h_str=time_str[0:2]
                m_str=time_str[3:5]
                s_str=time_str[6:8]
		#unix timestamp
                time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
                curs.execute("INSERT INTO B VALUES(NULL,?,%f,%f,%f,%f,%f,%f,%f,%f)"%(sar_B_str[i][1], sar_B_str[i][2], sar_B_str[i][3], sar_B_str[i][4], sar_B_str[i][5], sar_B_str[i][6], sar_B_str[i][8], sar_B_str[i][9]),(time_stamp,)); # 添加记录

#-----------------------------disk-----------------------
  for n in range(0,disk_row-1):
	  curs.execute("INSERT INTO DISK VALUES(NULL,?,?,%f,%f,%f,%f,%f,%f,%f,%f)"%(disk_tps[n],disk_rkbs[n],disk_wkbs[n],disk_areq[n],disk_aqu[n],disk_await[n],disk_svctm[n],disk_util[n]),(disk_time[n],disk_dev[n],));
#--------------------------------------task-------------------
  for n in range(0,task_row):
	  curs.execute("INSERT INTO TASK VALUES(NULL,? , %f, %f)"%(task_procs[n], task_cswchs[n]),(task_time[n],));
#---------------------------------------------IO---------------------------
  for n in range(0,io_row):
	  curs.execute("INSERT INTO IO VALUES(NULL,? , %f, %f, %f, %f,%f)"%(io_tps[n], io_rtps[n], io_wtps[n], io_breads[n], io_bwrtns[n]),(io_time[n],));
#-----------------------------------------------CHANGE--------------------------
  for n in range(0,change_row):
	   curs.execute("INSERT INTO CHANGE VALUES(NULL,? ,  %f, %f)"%(change_pswpins[n], change_pswpouts[n]),(change_time[n],));#插入
#--------------------------------------NETWORK----------------------------------
  for i in range(0,lines_DEV-1):
     count_DEV=len(sar_DEV_str[i].split())#获取每行分割数量
     sar_DEV_str[i]=sar_DEV_str[i].split()#分割每行
       #print(sar_DEV_str[i]) 
     #print(sar_DEV_str[i])
     #print(count_DEV)
     if count_DEV==10:#判断每行分割数量
        for j in range(0,count_DEV):
            try:
               sar_DEV_str[i][j]=float(sar_DEV_str[i][j])#转化为浮点数
            except ValueError:
               sar_DEV_str[i][j]=sar_DEV_str[i][j] 
               #p(year, month, day, h_str, m_str, s_str)
     
        if sar_DEV_str[i][0]!='平均时间:':#判断剔除平均时间
           if sar_DEV_str[i][1]!='IFACE':
              time_str=sar_DEV_str[i][0]
              h_str=time_str[0:2]
              m_str=time_str[3:5]
              s_str=time_str[6:8]
		#unix timestamp
              time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
              curs.execute("INSERT INTO DEV VALUES(NULL,?,?,%f,%f,%f,%f,%f,%f,%f,%f)"%(sar_DEV_str[i][2], sar_DEV_str[i][3], sar_DEV_str[i][4], sar_DEV_str[i][5], sar_DEV_str[i][6], sar_DEV_str[i][7], sar_DEV_str[i][8], sar_DEV_str[i][9]),(time_stamp,sar_DEV_str[i][1],)); # 添加记录
 
  for i in range(0,lines_EDEV-1):
       count_EDEV=len(sar_EDEV_str[i].split())#获取每行分割数量
     #print(count_EDEV)
     #print(sar_EDEV_str[i])
     
       sar_EDEV_str[i]=sar_EDEV_str[i].split()#分割每行
       #print( sar_EDEV_str[i])
       if count_EDEV==11:#判断每行分割数量
          for j in range(0,count_EDEV):
              try:
                 sar_EDEV_str[i][j]=float(sar_EDEV_str[i][j])#转化为浮点数
              except ValueError:
                 sar_EDEV_str[i][j]=sar_EDEV_str[i][j] 
            #print(sar_EDEV_str[i][j])
          if sar_EDEV_str[i][0]!='平均时间:':
             if sar_DEV_str[i][1]!='IFACE':
                time_str=sar_EDEV_str[i][0]
                h_str=time_str[0:2]
                m_str=time_str[3:5]
                s_str=time_str[6:8]
		#unix timestamp
                time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
                curs.execute("INSERT INTO EDEV VALUES(NULL,?,?,%f,%f,%f,%f,%f,%f,%f,%f,%f)"%(sar_EDEV_str[i][2], sar_EDEV_str[i][3], sar_EDEV_str[i][4], sar_EDEV_str[i][5], sar_EDEV_str[i][6], sar_EDEV_str[i][7], sar_EDEV_str[i][8], sar_EDEV_str[i][9], sar_EDEV_str[i][10]),(time_stamp,sar_EDEV_str[i][1],)); # 添加记录
 
#-------------run------------------
  for i in range(0,lines_q-1):
       count_q=len(sar_q_str[i].split())#获取每行分割数量
       sar_q_str[i]=sar_q_str[i].split()#分割每行
     #print(count_q)
     #print(sar_q_str[i])
       if count_q==7:#判断每行分割数量
          for j in range(0,count_q):
              try:
                 sar_q_str[i][j]=float(sar_q_str[i][j])#转化为浮点数
              except ValueError:
                 sar_q_str[i][j]=sar_q_str[i][j] 
            #print(sar_q_str[i][j])
          if sar_q_str[i][0]!='平均时间:':
             if sar_q_str[i][1]!='runq-sz':
                if sar_q_str[i][0]!='Linux': 
                   time_str=sar_q_str[i][0]
                   h_str=time_str[0:2]
                   m_str=time_str[3:5]
                   s_str=time_str[6:8]
		   #unix timestamp
                   time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)       
                   curs.execute("INSERT INTO q VALUES(NULL,?,%f,%f,%f,%f,%f,%f)"%(sar_q_str[i][1], sar_q_str[i][2], sar_q_str[i][3], sar_q_str[i][4], sar_q_str[i][5], sar_q_str[i][6]),(time_stamp,)); # 添加记录
#-----------------------------swp--------------------------------------
  for i in range(0,lines_S-1):
     count_S=len(sar_S_str[i].split())#获取每行分割数量
     sar_S_str[i]=sar_S_str[i].split()#分割每行
     #print(count_S)
     #print(sar_S_str[i])
     if count_S==6:#判断每行分割数量
        for j in range(0,count_S):
            try:
               sar_S_str[i][j]=float(sar_S_str[i][j])#转化为浮点数
            except ValueError:
               sar_S_str[i][j]=sar_S_str[i][j] 
            #print(sar_q_str[i][j])
        if sar_S_str[i][0]!='平均时间:':
           if sar_S_str[i][1]!='kbswpfree':  
               if sar_q_str[i][0]!='Linux': 
                  time_str=sar_S_str[i][0]
                  h_str=time_str[0:2]
                  m_str=time_str[3:5]
                  s_str=time_str[6:8]
		  #unix timestamp
                  time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)     
                  curs.execute("INSERT INTO S VALUES(NULL,?,%f,%f)"%(sar_S_str[i][3], sar_S_str[i][5]),(time_stamp,)); # 添加记录
#-----------------intr----------------------------------------------
  for i in range(0,lines_intr):
      count=len(sar_intr_str[i].split())
      sar_intr_str[i]=sar_intr_str[i].split()
     #print(sar_cpu_st
      for j in range(0,count):
           try:
              sar_intr_str[i][j]=float(sar_intr_str[i][j])#转化为浮点数
           except ValueError:
              sar_intr_str[i][j]=sar_intr_str[i][j]
      if count==3:
         if sar_intr_str[i][0]!='平均时间:':
            if sar_intr_str[i][1]=='sum':
               time_str=sar_intr_str[i][0]
               h_str=time_str[0:2]
               m_str=time_str[3:5]
               s_str=time_str[6:8]
		  #unix timestamp
               time_stamp=dt_stamp(year, month, day, h_str, m_str, s_str)
                    #print(time_stamp,sar_intr_str[i][1])     
               curs.execute("INSERT INTO intr VALUES(NULL,?,?,%f)"%(sar_intr_str[i][2]),(time_stamp,sar_intr_str[i][1],)); # 添加记录 
  num = getRC(curs)                       			      #获取游标所处理的行数
  conn.commit();
  '''
  print("__________CPU__________")
  curs.execute("SELECT * FROM CPU")
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12])
  curs.execute('DELETE FROM CPU WHERE id=%d' % 1)
  #curs.execute('DROP TABLE CPU')
  print("______________mhz__________")
  curs.execute("SELECT * FROM mhz")
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3])
  curs.execute('DELETE FROM mhz WHERE id=%d' % 1)
  #curs.execute('DROP TABLE mhz')

  print("__________DISK__________") 
  curs.execute("SELECT * FROM DISK")
  for row in curs.fetchall():
                  print(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
  curs.execute('DELETE FROM DISK WHERE id=%d' % 1)
  #curs.execute('DROP TABLE DISK')
  print("__________TASK__________") 
  curs.execute("SELECT * FROM TASK")
  for row in curs.fetchall():
                  print(row[0],row[1],row[2],row[3])
  curs.execute('DELETE FROM TASK WHERE id=%d' % 1)
  #curs.execute('DROP TABLE TASK')
  print("__________IO__________") 
  curs.execute("SELECT * FROM IO")
  for row in curs.fetchall():
		  print(row[0],row[1],row[2],row[3],row[4],row[5],row[6])
  curs.execute('DELETE FROM IO WHERE id=%d' % 1)                    
  #curs.execute('DROP TABLE IO')
  print("__________CHANGE__________") 
  curs.execute("SELECT * FROM CHANGE")
  for row in curs.fetchall():
		  print(row[0],row[1],row[2],row[3])
  curs.execute('DELETE FROM CHANGE WHERE id=%d' % 1)
  #curs.execute('DROP TABLE CHANGE')
  print("__________NETWORK__________") 
  curs.execute("SELECT * FROM DEV")
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
  curs.execute('DELETE FROM DEV WHERE id=%d' % 1)                   
  #curs.execute('DROP TABLE DEV')
  curs.execute("SELECT * FROM EDEV")
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
  curs.execute('DELETE FROM EDEV WHERE id=%d' % 1)                     
  #curs.execute('DROP TABLE EDEV')
  print("__________MEMORY__________") 
  curs.execute("SELECT * FROM memory")
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
  curs.execute('DELETE FROM memory WHERE id=%d' % 1)                   
  #curs.execute('DROP TABLE memory')
  curs.execute("SELECT * FROM B");                                
  for row in curs.fetchall():
                  print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
  curs.execute('DELETE FROM B WHERE id=%d' % 1)                    
  #curs.execute('DROP TABLE B')
  print("__________Runq-sz__________") 
  curs.execute("SELECT * FROM q");                                
  for row in curs.fetchall():
                   print (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])
  curs.execute('DELETE FROM q WHERE id=%d' % 1)
  #curs.execute('DROP TABLE q')

  print("__________%swp__________") 
  curs.execute("SELECT * FROM S")
  for row in curs.fetchall():
                   print (row[0],row[1],row[2],row[3])
  curs.execute('DELETE FROM S WHERE id=%d' % 1)
  #curs.execute('DROP TABLE S')
  print("__________intr__________") 
  curs.execute("SELECT * FROM intr")
  for row in curs.fetchall():
                   print (row[0],row[1],row[2],row[3])
  curs.execute('DELETE FROM intr WHERE id=%d' % 1)
  #curs.execute('DROP TABLE intr')
  '''
  exDb_dy_mtr()

  curs.close()                                                                       
  conn.close()


#--------------------将sqlite的数据导入到文件中-----------------2020.9-----------
def exDb_st_mtr():
	#连接数据库
	conn=sqlite3.connect('static_metrics.db')
	curs=conn.cursor()
	#打开文件
	output=open('static_metrics.txt', 'w')
	output.write('METRIC\t INFO\n')#表头
	curs.execute('SELECT * FROM STATIC_METRICS')
	for row in curs.fetchall():
		print(row[0], row[1])
		output.write(row[0]+'\t'+row[1]+'\n')
	output.close()
	curs.close()

def exDb_dy_mtr():
	#连接数据库
	conn=sqlite3.connect('somedata.db')
	curs=conn.cursor()
	#打开文件
	output_cpu=open('CPU_metrics.txt', 'w')
	output_mhz=open('MHZ_metrics.txt', 'w')
	output_memory=open('MEMORY_metrics.txt', 'w')
	output_disk=open('DISK_metrics.txt', 'w')
	output_dev=open('DEV_metrics.txt', 'w')
	output_edev=open('EDEV_metrics.txt', 'w')
	output_task=open('TASK_metrics.txt', 'w')
	output_io=open('IO_metrics.txt', 'w')
	output_change=open('CHANGE_metris.txt', 'w')
	output_B=open('B_metrics.txt', 'w')
	output_q=open('Q_metrics.txt', 'w')
	output_S=open('S_metrics.txt', 'w')
	output_intr=open('INTR_metrics.txt', 'w')
	
	curs.execute('SELECT * FROM CPU')
	for row in curs.fetchall():
		output_cpu.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])+'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\t'+str(row[10])+'\t'+str(row[11])+'\t'+str(row[12])+'\n')
	
	curs.execute("SELECT * FROM mhz")
	for row in curs.fetchall():
		output_mhz.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')
  	#for row in curs.fetchall():
		#output_mhz.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')
	
	curs.execute("SELECT * FROM DISK")
	for row in curs.fetchall():
		output_disk.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])
                  +'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\t'+str(row[10])+'\n')
	
	curs.execute("SELECT * FROM TASK")
	for row in curs.fetchall():
		output_task.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')
	
	curs.execute("SELECT * FROM IO")                            
	for row in curs.fetchall():
		output_io.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])+'\t'+str(row[5])+'\t'+str(row[6])+'\n')
	
	curs.execute("SELECT * FROM CHANGE")
	for row in curs.fetchall():
		output_change.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')
	
	curs.execute("SELECT * FROM DEV")
	for row in curs.fetchall():
		output_dev.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])
                  +'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\t'+str(row[10])+'\n')
	
	curs.execute("SELECT * FROM EDEV")
	for row in curs.fetchall():
		output_edev.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])
                  +'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\t'+str(row[10])+'\n')
	
	curs.execute("SELECT * FROM memory")
	for row in curs.fetchall():
		output_memory.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])
                  +'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\t'+str(row[10])+'\n')
	
	curs.execute("SELECT * FROM B")
	for row in curs.fetchall():
		output_B.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+
                  str(row[4])+'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\t'+str(row[8])+'\t'+str(row[9])+'\n')
	
	curs.execute("SELECT * FROM q")
	for row in curs.fetchall():
		output_q.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\t'+str(row[4])+'\t'+str(row[5])+'\t'+str(row[6])+'\t'+str(row[7])+'\n')
	
	curs.execute("SELECT * FROM S")
	for row in curs.fetchall():
		output_S.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')
	
	curs.execute("SELECT * FROM intr")
	for row in curs.fetchall():
		output_intr.write(str(row[0])+'\t'+str(row[1])+'\t'+str(row[2])+'\t'+str(row[3])+'\n')

	output_cpu.close()
	output_mhz.close()
	output_memory.close()
	output_disk.close()
	output_dev.close()
	output_edev.close()
	output_task.close()
	output_io.close()
	output_change.close()
	output_B.close()
	output_q.close()
	output_S.close()
	output_intr.close()
	curse.close()

#END

