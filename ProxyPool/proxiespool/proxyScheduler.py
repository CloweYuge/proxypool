import time
from multiprocessing import Process
from .proxyApi import app
from .proxyCrawl import Getter
from .proxyTester import Tester
from .proxySetting import TESTER_CYCLE, GETTER_CYCLE, TESTER_ENABLED, GETTER_ENABLED, API_ENABLED, API_PORT

# TESTER_CYCLE = 20
# GETTER_CYCLE = 20
# TESTER_ENABLED = True
# GETTER_ENABLED = True
# API_ENABLED = True


class Scheduler():
    def scheduler_tester(self, cycle=TESTER_CYCLE):
        """
        定时测试代理
        :param cycle:
        :return:
        """
        tester = Tester()
        while True:
            print('启动测试器')
            tester.run()
            time.sleep(cycle)

    def scheduler_getter(self, cycle=GETTER_CYCLE):
        """
        定时获取代理
        :param cycle:
        :return:
        """
        getter = Getter()
        while True:
            print('启动获取器')
            getter.run()
            time.sleep(cycle)

    def scheduler_api(self):
        """
        开启接口
        :return:
        """
        print('web接口开启')
        app.run(port=API_PORT)

    def run(self):
        print('代理池开始运行')
        if TESTER_ENABLED:
            tester_process = Process(target=self.scheduler_tester)
            tester_process.start()

        if GETTER_ENABLED:
            getter_process = Process(target=self.scheduler_getter)
            getter_process.start()

        if API_ENABLED:
            api_process = Process(target=self.scheduler_api)
            api_process.start()

if __name__ == '__main__':
    testrun = Scheduler()
    testrun.run()
