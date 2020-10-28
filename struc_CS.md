# CS模块

____

## 模块应该具备以下功能：

* 接收来自LoadRunner模块以及SAR模块的就绪提示；
* 向LoadRunner发送加压命令，并带上负载水平的参数；
* 向sar数据采集模块发送数据采集命令，并接收来自数据采集模块的数据；
* 从功耗仪读取需要的功耗数据；
* 数据处理，即将数据采集模块的数据与功耗仪中的数据根据时标进行对齐。

---

## 结构设计

​	getReadyFromLR()

​    getReadyFromSAR()

​	for a in range coresNum:

​	    for b in range freqStepNum:

​			for c in cpuStepNum:

​				for d in memStepNum:

​					for e in diskStepNum:

​						for f in netStepNum:

​							para[]=transCounterIntoParameter(a, b, c, d, e, f)

​							sendParaToLR(para[])

​							wait

​							sendCollectInstrucToSAR()

​							getDataFromSAR()

​							getDataFromPower()

​							sendStopToLR()

​							dataProcess(sarData, powerData)