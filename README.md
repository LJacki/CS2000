# python 连接CS2000 
记录CS2000设备使用串口连接以及相关控制。

CS2000是一台分管辐射亮度计，也就是可以测量光源的亮度。详细的规格网址参考[CS2000/CS-2000A](https://www.konicaminolta.com.cn/instruments/products/light/spectroradiometer/cs2000/index.html) ，所有信息以柯尼卡美能达官网的参数以及使用手册为主。

## 使用目的及环境

当前的使用目的是使用PC端控制CS2000，测量屏幕的亮度数据。

PC端使用Python，在Win10环境下开发；

需要额外安装的模块：pySerial；

## 设备连接方法

这台设备是支持USB1.1 Full-Speed和RS-232C的。其配套的软件CS-S10是使用的USB1.1接口，如果安装了软件，也就相当于安装了对应驱动。当然，我这里则是使用了配置串行通讯端口`COM Port`(Cluster Communication Port)。

CS2000支持的通讯设定如下：

![image-20210614110048426](https://gitee.com/sharewow/pic_repo/raw/master/img/image-20210614110048426.png)

这里选用波特率115200，数据长度8 bits， 无校验，1 bit停止位的设定；至于Hardware(RTS/CTS)，即Require To Send和Clear To Send信号，这里先不做考虑。

## 程序主体流程

1. 获取电脑COM列表；
2. 连接并打开CS2000的设备端口；
3. 设备初始化（设定控制模式，关闭测试按键操作，设定同步模式等）；
4. 单次测量并获取测量值；
5. 关闭串口；

接下来就开始结合手册进行操作。

### 获取端口

需要引入`serial.tools.list_ports`模块：

```python
def port_list():
    """
    获取电脑端口列表
    :return: 端口列表
    """
    pl = serial.tools.list_ports.comports()
    # print(pl)
    print("Port List:")
    for item in pl:
        print("{}\t\t:\t{}".format(item.usb_description(), item.manufacturer))
```

获取端口列表后，可以打印端口的描述和制造商，用于区分多个端口。

### 连接端口

需要引入`serial`模块：

```python
def connect_com(port, baudrate=115200, timeout=0):
    """
    配置串口参数并进行连接；
    :param port: 端口号，“COM1”
    :param baudrate: 波特率，115200
    :param timeout: 超时时间，0
    :return: 连接好的串口，ser
    """
    # noinspection PyBroadException
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Port\t\t:\t{}".format(ser.name))
        print("Baudrate\t:\t{}".format(ser.baudrate))
        print("Status\t\t:\t{} Connect Successful!".format(port))
        return ser
    except Exception:
        print("Status\t\t:\t\t\tConnect COM Failed!")
```

定义的函数，返回打开串口之后的对象。

### 发送格式

#### 分隔符

使用PC发送命令到测量设备的时候，需要使用如下分隔符：

![image-20210614112307699](F:\GIT_HERE\CS2000\README.assets\image-20210614112307699.png)

`CR`, `LF`对应的ASCII的`0x0D`和`0x0A`；也就是在命令结束后要加分隔符进行分割；

#### 数据字符格式

发送的数据中，数字发送，必须要跟数字的字符一样。比如发送十进制数据`886`，就需要发送对应的字符`886`。如果需要输入的字符长度少，需要用空格补齐。

#### 超时

PC通信的超时设定至少要10s。这里可以理解为设备测量亮度是需要积分时间的，比如说测试比较暗的画面，需要长时间的积分，因此测量的返回数据需要对应延迟很长时间，因此超时设定为至少10s。

实际使用的情况中，比较暗的画面可能需要超过7s的测量时间。

### 初始化

初始化包含以下以几个环节，包括设置远端模式（SCMS），关闭测量按键（MSWE），设定同步模式（SCMS）等；这里仔细参考手册，很容易就能理解，下面就直接贴出代码。

```python
def remote_mode(ser):
    """
    对cs2000进行远程控制设置
    :param ser: cs2000的串口
    :return: None
    """
    data = b'RMTS,1\n'
    tx_data(ser, data)
    if rx_data(ser)[0] == "OK00":
        print("Status\t\t:\tRemote Mode Setting OK!")
    else:
        print("Status\t\t:\tRemote Mode Setting ERROR!")


def meas_key_off(ser):
    """
    关闭cs2000设备上的measure按键控制
    :param ser: cs2000的串口
    :return: None
    """
    data = b'MSWE,0\n'
    tx_data(ser, data)
    if rx_data(ser)[0] == "OK00":
        # print("Status\t\t:\tMeasure Key Disable OK!")
        pass
    else:
        print("Status\t\t:\tMeasure Key Disable ERROR!")


def sync_mode_set(ser, freq):
    """
    同步模式设定
    :param ser: cs2000的串口
    :param freq: 频率，单位Hz
    :return: None
    """
    mode = b'1,'
    freq = freq.encode()
    data = b'SCMS,' + mode + freq + b'00\n'
    tx_data(ser, data)
    if rx_data(ser)[0] == "OK00":
        print("Status\t\t:\tSync Mode is {}, freq is {}Hz!".format(mode, freq))
        pass
    else:
        print("Status\t\t:\tMeasure Key Disable ERROR!")


def sync_mode_read(ser):
    """
    同步模式读取
    :param ser: cs2000的串口
    :return: None
    """
    sync_mode_dict = {"0": "No sync",
                      "1": "Internal sync",
                      "2": "External sync"}
    data = b'SCMR\n'
    tx_data(ser, data)
    rdata = rx_data(ser)
    if rdata[0] == "OK00":
        print("Status\t\t:\tSync Mode is {}. ".format(sync_mode_dict[rdata[1]]))
        if rdata[1] == "1":
            print("Status\t\t:\tSync frequency is {}Hz. ".format(rdata[2][:-2]))
        pass
    else:
        print("Status\t\t:\tSync Mode read ERROR!")


def dev_init(ser):
    """
    cs2000设备进行初始化，包含设置为远程控制，关闭测量按键，设置同步模式，查询同步模式数据
    :param ser: cs2000的串口
    :return: None
    """
    remote_mode(ser)
    meas_key_off(ser)
    sync_mode_set(ser, SYNC_FREQ)
    sync_mode_read(ser)

```

**注意**：这里每次发送命令之后，设备均会返回数据。如若返回的是`OK00`，则说明命令发送和接收都没有出现问题，如果返回的指令有`ERxx`等字样，需要根据手册中的错误代码列表查询错误原因，并进行改正。

### 测量数据

测量数据需要先发送测量指令，等待返回测量时间，等待测量结束；

再发送测量数据读取指令。

```python
def measure(ser):
    """
    向cs2000发出测量的命令
    :param ser: cs2000的串口
    :return: None
    """
    data = b'MEAS,1\n'
    tx_data(ser, data)
    rdata = rx_data(ser)
    if rdata[0] == "OK00":
        # print("Status\t\t:\tMeasure time is {}s".format(rdata[1]))
        pass
    else:
        print("Status\t\t:\tMeasure CMD ERROR Code {}".format(rdata[0]))

    rdata_1 = rx_data(ser)
    if rdata_1[0] == "OK00":
        # print("Status\t\t:\tMeasurement completed!")
        pass
    else:
        print("Status\t\t:\tMeasure Wait ERROR Code {}".format(rdata_1[0]))


def lv_read(ser):
    """
    向cs2000发出测量的命令
    :param ser: cs2000的串口
    :return: 亮度值lv
    """
    data = b'MEDR,2,0,101\n'
    tx_data(ser, data)
    rdata = rx_data(ser)
    if rdata[0] == "OK00":
        # print("Status\t\t:\tLuminance is {} cd/m²".format(rdata[1]))
        return rdata[1]
    else:
        print("Status\t\t:\tLuminance Read ERROR Code {}".format(rdata[0]))
        return None


def get_lv(ser):
    """
    获取亮度值
    :param ser: cs2000的串口
    :return: 亮度值，单位cd/m²
    """
    measure(ser)
    return lv_read(ser)


def xylv_read(ser):
    """
    向cs2000发出测量的命令
    :param ser: cs2000的串口
    :return: 色坐标，X，Y，亮度，LV
    """
    data = b'MEDR,2,0,2\n'
    tx_data(ser, data)
    rdata = rx_data(ser)
    if rdata[0] == "OK00":
        print("Status\t\t:\tX，Y，LV are {} {} {}".format(rdata[1], rdata[2], rdata[3]))
        return rdata[1:]
    else:
        print("Status\t\t:\tMeasure ERROR!")
        return None


def get_xylv(ser):
    """
    获取色坐标X，Y和亮度LV。
    :param ser: cs2000的串口
    :return: 色坐标，X，Y，亮度，LV
    """
    measure(ser)
    return xylv_read(ser)
```

其中，返回数据的格式需要根据发送的指令进行解析，对应在Datasheet中也有介绍。

### 串口收发数据的函数

对于串口收发数据，也封装了一层函数，方便调用：

```python
def tx_data(ser, data):
    # noinspection PyBroadException
    try:
        ser.write(data)
        # print("Status\t\t:\tSend OK!")
    except Exception:
        print("Status\t\t:\tSend ERROR!")


def rx_data(ser):
    # noinspection PyBroadException
    try:
        rdata = ser.readline().decode("utf-8").replace("\n", "").split(",")
        # print("Status\t\t:\tReceived {}".format(rdata))
        return rdata
    except Exception:
        print("Status\t\t:\tReceive ERROR!")

```

### 串口关闭

串口使用之后一定要进行合理的关闭，防止多个程序运行，出现连接问题。

```python
def serial_close(ser):
    """
    关闭串口连接
    :return: None
    """
    # noinspection PyBroadException
    try:
        ser.close()
        print("Port {} has been closed!".format(ser.name))
    except Exception:
        print("----serial_close failed!")

```

### 主函数

所有的参数传递，都是将`产生的串口对象`作为参数传递。

```python
if __name__ == '__main__':

    port_list()

    cs2000 = connect_com("COM1", timeout=5)

    dev_init(cs2000)

    get_lv(cs2000)
    get_xylv(cs2000)

    serial_close(cs2000)
```

## 写在后面

设备调试的要义在于，**一切操作要参考Datasheet：cs_2000_technicalnote_en**，可以在官网支持中下载到。熟悉了手册之后，后面的调试环节可以节省很多时间，调制的过程也会非常顺利。这里例举几个调试过程中遇到的问题：

1. 合理设定超时（要根据最长的测量时间设定），在发送数据之后就可以等待接收数据；
2. 这里的分隔符使用的就是`\n`，转换为`byte类型`后进行串口发送；
3. 一些模式设定可以只进行一次设定，不需要每次上电都进行设定，为保险起见，统一放在初始化里面；
4. 暗光环境下测试暗光源，需要的时间会很长，手动测试版有`24s`之多，亮光源的测试时间在`1s`一次左右；
5. 程序中将**串口**直接作为参数传递有些不妥，可以将该模块改为`class`；

后面如果遇到了其他问题也会在此更新。

本项目源码地址：https://github.com/LJacki/CS2000

2021-6-14.