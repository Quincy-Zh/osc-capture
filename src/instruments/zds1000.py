import usb.core
import usb.util
import time


class ZDS:
    def __init__(self):
        self.dev = usb.core.find(idVendor=0x04CC, idProduct=0x121C)

        if self.dev:
            self.dev.set_configuration()

    def kill(self):
        if self.dev:
            usb.util.dispose_resources(self.dev)

    def is_device_ready(self):
        return self.dev is not None

    def __write(self, cmd, timeout=1000):
        if self.dev is None:
            return -2

        data = cmd.encode("ascii") + b"\n"
        sz = -1
        try:
            sz = self.dev.write(0x01, data, timeout)
        except usb.core.USBError as ex:
            print("USBError /w:", ex.strerror.decode("gbk"))
        except Exception as ex:
            print(ex)

        return sz

    def __exec(self, cmd, size, timeout=1000):
        sz = self.__write(cmd, timeout)
        if sz < 0:
            return None

        rc = None
        try:
            rc = self.dev.read(0x81, size, timeout)
        except usb.core.USBError as ex:
            print("USBError /r:", ex.strerror.decode("gbk"))
        except Exception as ex:
            print(ex)

        return rc

    def opc(self):
        x = self.__exec("*OPC?", 5, 5000)
        if x:
            return int(x.tobytes())
        else:
            return None

    def capture(self):
        sz = self.__write(":PRINt")
        if sz < 0:
            return None

        time.sleep(5)

        x = self.__exec(":DISPlay:DATA?", 1024 * 1024 * 10, 5000)
        if x:
            return x.tobytes()
        else:
            return None


def save_definite_length_block_data(data, filepath):
    if data[0] != 35:
        return -1

    w = data[1] - 0x30
    length = int(data[2 : w + 2].decode("ascii"))
    with open(filepath, "wb") as fd:
        fd.write(data[w + 2 : w + 2 + length])

    return length


if __name__ == "__main__":
    zds = ZDS()

    if zds.is_device_ready():
        cap = zds.capture()
        sz = save_definite_length_block_data(cap, "a.bmp")
        print(sz)

        zds.kill()
