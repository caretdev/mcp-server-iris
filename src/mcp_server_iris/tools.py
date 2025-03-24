def raise_on_error(iris, status):
    if status and status[0] != "1":
        message = iris.classMethodValue("%SYSTEM.Status", "GetErrorText", status)
        raise Exception(message)


class transaction:
    def __init__(self, iris):
        self.iris = iris

    def __enter__(self):
        self.iris.tStart()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.iris.tRollback()
        else:
            self.iris.tCommit()
