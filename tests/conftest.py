import pytest
from testcontainers.iris import IRISContainer


def pytest_addoption(parser):
    group = parser.getgroup("iris")

    group.addoption(
        "--embedded",
        action="store_true",
        help="Use embedded mode",
    )

    group.addoption(
        "--iris-host",
        action="store",
        default="localhost",
        help="Hostname",
    )

    group.addoption(
        "--iris-port",
        action="store",
        default=1972,
        type=int,
        help="Port",
    )

    group.addoption(
        "--iris-namespace",
        action="store",
        default="USER",
        help="Namespace",
    )

    group.addoption(
        "--iris-username",
        action="store",
        default="_SYSTEM",
        help="Username",
    )

    group.addoption(
        "--iris-password",
        action="store",
        default="SYS",
        help="Password",
    )

    group.addoption(
        "--container",
        action="store",
        default=None,
        type=str,
        help="Docker image with IRIS",
    )


def pytest_configure(config: pytest.Config):
    global iris
    iris = None
    if not config.option.container:
        return
    config.option.embedded = False
    print("Starting IRIS container:", config.option.container)
    try:
        iris = IRISContainer(
            config.option.container,
            username="test",
            password="test",
            namespace="TEST",
        )
        iris.start()
        print("Started on port:", iris.get_exposed_port(1972))
        print(iris.get_connection_url())
        config.option.iris_host = "localhost"
        config.option.iris_username = iris.username
        config.option.iris_password = iris.password
        config.option.iris_namespace = iris.namespace
        config.option.iris_port = int(iris.get_exposed_port(1972))
    except Exception as ex:
        iris = None
        pytest.exit("Failed to start IRIS container: " + str(ex))


def pytest_unconfigure(config):
    global iris
    if iris:
        print("Stopping IRIS container")
        iris.stop()
