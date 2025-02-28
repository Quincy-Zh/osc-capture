# 获取示波器截图

import os
import logging
import pyvisa
from instruments import dso_x_3024t, mdo32, mxr208a, zds1000, utils


logger = logging.getLogger("Capture")


def zds_cap(a, param):
    z = zds1000.ZDS()

    if not z.is_device_ready():
        return ""

    cap = z.capture()
    if cap is None:
        return ""

    filename, ts = utils.get_filepath()
    filepath = os.path.join(param["output"], filename + ".bmp")
    zds1000.save_definite_length_block_data(cap, filepath)

    z.kill()

    if not utils.addWaterMark(filepath, ts, x=5, y=10):
        logger.warning("添加水印失败~")

    return filepath


class Capture:
    prepFuncMap = {
        "DSO-X 3024T": dso_x_3024t.prepare,
        "MDO32": mdo32.prepare,
        "MXR208A": mxr208a.prepare,
    }
    capFuncMap = {
        "DSO-X 3024T": dso_x_3024t.capture,
        "MDO32": mdo32.capture,
        "MXR208A": mxr208a.capture,
        "ZDS1000": zds_cap,
    }
    ctrlFuncMap = {
        "DSO-X 3024T": dso_x_3024t.ctrl,
    }

    def __init__(self, output_dir) -> None:
        #
        self.res = None
        self.fn = None
        self.fn_ctrl = None
        self.param = {"output": output_dir}

    def is_connected(self):
        return self.res is not None

    def disconnect(self):
        if self.res:
            if not isinstance(self.res, str):
                self.res.close()

    def connect_to(self, address, model):
        if model not in self.capFuncMap:
            logger.warning('尚未支持的设备: "{}"'.format(model))
            return (False, "尚未支持的设备")

        self.fn = self.capFuncMap[model]

        if model in self.ctrlFuncMap:
            self.fn_ctrl = self.ctrlFuncMap[model]

        if model == "ZDS1000":
            self.res = model
            return (True, "")

        self.rm = pyvisa.ResourceManager()

        err = ""
        try:
            self.res = self.rm.open_resource(address)
        except Exception as ex:
            logger.warning(str(ex))
            err = "连接设备时发生错误"

        if err == "":
            if model in self.prepFuncMap:
                prep = self.prepFuncMap[model]

                err_, param = prep(self.res)
                if err_ != "":
                    logger.warning(err_)
                    self.disconnect()
                    err = "内部错误：" + err_
                else:
                    self.param.update(param)
                #
            #
        #

        return (err == "", err)

    def exec(self):
        err = ""
        path = ""

        if not self.is_connected():
            err = "未连接"
        else:
            try:
                path = self.fn(self.res, self.param)
            except Exception as ex:
                err = "连接时发生错误"
                logger.warning(str(ex))

        return (err, path)

    def ctrl(self, cmd: str) -> int:
        if not self.is_connected():
            err = -1

        if self.fn_ctrl is None:
            err = 1
        else:
            err = self.fn_ctrl(self.res, cmd)

        return err


if __name__ == "__main__":
    eq = Capture(".")
    ok, err = eq.connect_to("USB0::0x2A8D::0x9007::MY60320114::INSTR", "MXR208A")

    if ok:
        err, f = eq.exec()
        print("# Capture:", err, f)
    else:
        print("! No Connection", err)
