# 载入 serial库，install库名为pyserial
import serial
import serial.tools.list_ports
import time

SYNC_FREQ = "60"


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


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# if __name__ == '__main__':
#
#     port_list()
#
#     cs2000 = connect_com("COM1", timeout=5)
#     # panel = connect_com("COM3")
#
#     dev_init(cs2000)
#
#     get_lv(cs2000)
#     get_xylv(cs2000)
#
#     serial_close(cs2000)
