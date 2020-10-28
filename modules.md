# 各模块分工

 

![img](file:///C:/Users/可大乖人/AppData/Local/Temp/msohtmlclip1/01/clip_image002.jpg)

 

## CS

1. 向LR发送加压水平的参数，接收LR已开始加压的提示；

2. 向SAR发送采集数据的命令，接收来自SAR的数据；

3. 考虑将何时采集的数据作为最终的结果；

4. 从功耗仪读取数据，将SAR的数据与Power数据根据时间戳进行对齐；

 

## LoadRunner

提供一个黑盒，CS向其提供各部件的加压水平的参数，然后执行加压到目标水平，加压开始后向CS发送提示。

 

## SPEC

研究SPEC加压过程，需要弄清楚在某个时刻SPEC在什么阶段做什么工作，考虑如何用SPEC为我们所用。

 

## SAR

收到CS的读取命令后采集数据，将一组数据按指定的格式发送给CS。