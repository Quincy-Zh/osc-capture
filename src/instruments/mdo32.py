#
# Tektronix 3 Series MDO Oscilloscopes
import os
from datetime import datetime
from .utils import get_filepath


def prepare(instrument):
    # 校时，是否成功也无所谓...
    now = datetime.now()
    try:
        cmd = now.strftime('TIMe "%H:%M:%S"')
        instrument.write(cmd)

        cmd = now.strftime('DATE "%Y-%m-%d"')
        instrument.write(cmd)

    except Exception as ex:
        print(ex)

    # 测试哪个驱动器可用
    rc = ""
    dirname = now.strftime("TEM_%Y%m%d_%H%M%S")
    for driver in ("E:", "F:", "G:"):
        res = ""
        try:
            path = driver + "/" + dirname
            # print('Mkdir:', path)

            instrument.write('FILESYSTEM:MKDIR "{}"'.format(path))
            instrument.write('FILESystem:CWD "{}"'.format(path))
            instrument.write(
                'FILESystem:WRITEFile "{}/aa.txt", #213Hello, World!'.format(path)
            )

            res += instrument.query("FILESystem:DIR?")
            instrument.write('FILESystem:DELEte "{}"'.format(path))
        except Exception as ex:
            print(ex)

        res = res.strip()

        if res != '""':
            rc = driver
            # print('[', res, ']-->', driver)
            break

    if rc == "":
        # 没有驱动器可用
        return ("MDO32 示波器需要外部存储设备，但是没有任何可用的设备", None)
    else:
        return ("", {"driver": rc})


def capture(instrument, param):
    if param is None or "driver" not in param or "output" not in param:
        return ""

    filepath = param["driver"] + "/tmp.png"

    cmd = 'SAVe:IMAGe "{}"'.format(filepath)

    try:
        res = instrument.write(cmd)

        cmd = 'FILESystem:READFile "{}"'.format(filepath)
        res = instrument.write(cmd)
    except Exception as ex:
        print(ex)
        return ""

    filename, _ = get_filepath()
    filepath = os.path.join(param["output"], filename + ".png")
    fd = open(filepath, "wb")

    while True:
        try:
            res = instrument.read_raw(1024)
            fd.write(res)
        except Exception as ex:
            # print(ex)
            break

    fd.close()

    return filepath
