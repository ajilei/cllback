import time


def timmer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        stop = time.time()
        print('函数运行时长', stop - start, '秒')
        return res

    return wrapper
