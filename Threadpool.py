import threading, queue

#自定义一个线程池
class Threadpool(object):
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._q = queue.Queue(self.maxsize)
        for i in range(self.maxsize):
            self._q.put(threading.Thread)
    #从queue取出线程
    def getThread(self):
        return self._q.get()
    #添加线程到queue中
    def addThread(self):
        self._q.put(threading.Thread)
