#
# DSO-X 3024T
import pyvisa
from datetime import datetime
from .utils import get_filepath


def prepare(instrument):
    # 校时，是否成功也无所谓...
    now = datetime.now()
    try:
        cmd = now.strftime(":SYSTem:TIME %H,%M,%S")
        instrument.write(cmd)

        cmd = now.strftime(":SYSTem:DATE %Y,%m,%d")
        instrument.write(cmd)

        instrument.write(":HARDcopy:INKSaver OFF")

    except Exception as ex:
        print(ex)

    return ("", {})


def ctrl(instrument, cmd):
    # 'INKSAVE:ON'

    items = cmd.upper().split(":")

    if items[0] != "INKSAVE":
        return -2

    if len(items) > 1 and items[1] == "OFF":
        _cmd = ":HARDcopy:INKSaver OFF"
    else:
        _cmd = ":HARDcopy:INKSaver ON"

    res = -1
    try:
        instrument.write(_cmd)
        res = 0
    except Exception as ex:
        print(ex)

    return res


def capture(instrument, param):
    instrument.query_delay = 0.5

    try:
        instrument.write(":DISPlay:DATA? PNG,COlor")
    except Exception as ex:
        print(ex)
        return ""

    cnt = 0
    status = 0
    while status == 0 and cnt < 20:
        try:
            res = instrument.read_raw()
            status = 1
        except pyvisa.errors.VisaIOError as ex:
            if ex.error_code == pyvisa.constants.VI_ERROR_TMO:
                status = 0
            else:
                print(ex)
                status = -1
        except Exception as ex:
            print(ex)
            status = -1

        cnt += 1

    # print('Status:', status, res[0])
    if status <= 0:
        return ""

    if res[0] != 35:  # b'#':
        print(res[:10])
        return ""

    w = res[1] - 0x30

    f = get_filepath(param["output"])
    with open(f, "wb") as fd:
        fd.write(res[w + 2 :])

    return f
