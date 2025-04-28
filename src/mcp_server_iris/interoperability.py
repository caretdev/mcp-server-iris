from enum import Enum
from mcp_server_iris.mcpserver import Context
from mcp_server_iris.tools import transaction, raise_on_error
from iris import IRISReference


class ProductionStatus(Enum):
    Unknown = 0
    Running = 1
    Stopped = 2
    Suspended = 3
    Troubled = 4
    NetworkStopped = 5
    ShardWorkerProhibited = 6


log_types = [
    "ASSERT",
    "ERROR",
    "WARNING",
    "INFO",
    "TRACE",
    "ALERT",
]


class LogType(Enum):
    Assert = 1
    Error = 2
    Warning = 3
    Info = 4
    Trace = 5
    Alert = 6


def production_items_status(iris, running: bool, name: str) -> list[str]:
    result = []
    namespace = iris.classMethodString("%SYSTEM.Process", "NameSpace")
    prod = iris.classMethodObject("Ens.Config.Production", "%OpenId", name)
    if not prod:
        raise ValueError(f"Production {name} not found")
    items = prod.getObject("Items")
    for i in range(1, items.invokeInteger("Count") + 1):
        item = items.invokeObject("GetAt", i)
        item_name = item.getString("Name")
        status_info = []
        enabled = item.getBoolean("Enabled")
        status_info += [f"Enabled={enabled}"]
        if enabled:
            val = iris.getString(
                "^IRIS.Temp.EnsHostMonitor", namespace, item_name, "%Status"
            )
            status_info += [f"Status={val}"]

        result.append(f"{item_name}: " + "; ".join(status_info))
    return result


def init(server, logger):
    @server.tool(description="Create an Interoperability Production")
    async def interoperability_production_create(name: str, ctx: Context) -> bool:
        if "." not in name:
            raise ValueError(
                "Production name must in format packagenamespace.productionname, where packagenamespace can have multiple parts separated by dots"
            )
        iris = ctx.iris
        with transaction(iris):
            prod = iris.classMethodObject(
                "%Dictionary.ClassDefinition", "%OpenId", name
            )
            if prod:
                raise ValueError(f"Class {name} already exists")
            logger.info(f"Creating Interoperability Production: {name}")
            prod = iris.classMethodObject("Ens.Config.Production", "%New", name)
            raise_on_error(iris, prod.invokeString("SaveToClass"))
            raise_on_error(iris, prod.invokeString("%Save"))
            raise_on_error(
                iris, iris.classMethodString("%SYSTEM.OBJ", "Compile", name, "ck-d")
            )
            return True

    @server.tool(description="Status of an Interoperability Production")
    async def interoperability_production_status(
        ctx: Context,
        name: str = None,
        full_status: bool = False,
    ) -> str:
        logger.info("Interoperability Production Status" + f": {name}" if name else "")
        iris = ctx.iris
        refname = IRISReference(iris)
        refname.setValue(name)
        refstatus = IRISReference(iris)
        raise_on_error(
            iris,
            iris.classMethodString(
                "Ens.Director", "GetProductionStatus", refname, refstatus
            ),
        )
        if not refname.getValue():
            raise ValueError("No running production found")
        name = refname.getValue()
        status = ProductionStatus(int(refstatus.getValue()))
        reason = IRISReference(iris)
        needsupdate = iris.classMethodBoolean(
            "Ens.Director", "ProductionNeedsUpdate", reason
        )
        reason_update = (
            f"Production needs update: {reason.getValue()}" if needsupdate else ""
        )

        if status == ProductionStatus.Running and full_status:
            items_status = production_items_status(
                iris, status == ProductionStatus.Running, name
            )
            return f"Production {name} is running with items: \n{"\n".join(items_status)}\n{reason_update}"
        return f"Production {name} with status: {status.name}\n{reason_update}"

    @server.tool(description="Start an Interoperability Production")
    async def interoperability_production_start(
        ctx: Context,
        name: str = None,
    ) -> str:
        logger.info(
            "Starting Interoperability Production" + f": {name}" if name else "."
        )
        iris = ctx.iris
        raise_on_error(
            iris,
            iris.classMethodString(
                "Ens.Director", "StartProduction", *([name] if name else [])
            ),
        )
        refname = IRISReference(iris)
        name and refname.setValue(name)
        refstatus = IRISReference(iris)
        status = iris.classMethodString(
            "Ens.Director", "GetProductionStatus", refname, refstatus
        )
        if not name:
            name = refname.getValue()
        if (
            status != "1"
            or ProductionStatus(int(refstatus.getValue())) != ProductionStatus.Running
        ):
            raise ValueError(f"Production {name} not started.")
        return "Started production"

    @server.tool(description="Stop an Interoperability Production")
    async def interoperability_production_stop(
        ctx: Context,
        timeout: int = None,
        force: bool = False,
    ) -> str:
        logger.info("Sopping Interoperability Production.")
        iris = ctx.iris
        raise_on_error(
            iris,
            iris.classMethodString(
                "Ens.Director", "StopProduction", timeout or 10, force
            ),
        )
        return "Stopped production"

    @server.tool(description="Recover an Interoperability Production")
    async def interoperability_production_recover(
        ctx: Context,
    ) -> str:
        logger.info("Recovering Interoperability Production")
        iris = ctx.iris
        raise_on_error(
            iris, iris.classMethodString("Ens.Director", "RecoverProduction")
        )
        return "Recovered"

    @server.tool(description="Check if an Interoperability Production needs update")
    async def interoperability_production_needsupdate(
        ctx: Context,
    ) -> str:
        logger.info("Checking if Interoperability Production needs update")
        iris = ctx.iris
        reason = IRISReference(iris)
        result = iris.classMethodBoolean(
            "Ens.Director", "ProductionNeedsUpdate", reason
        )
        if result:
            raise ValueError(f"Production needs update: {reason.getValue()}")
        return "Production does not need update"

    @server.tool(description="Update Interoperability Production")
    async def interoperability_production_update(
        ctx: Context,
        timeout: int = None,
        force: bool = False,
    ) -> str:
        iris = ctx.iris
        raise_on_error(
            iris,
            iris.classMethodString("Ens.Director", "UpdateProduction", timeout, force),
        )
        return "Production updated"

    @server.tool(description="Get Interoperability Production logs")
    async def interoperability_production_logs(
        ctx: Context,
        item_name: str = None,
        limit: int = 10,
        log_type_info: bool = False,
        log_type_alert: bool = False,
        log_type_error: bool = True,
        log_type_warning: bool = True,
    ) -> str:
        logs = []
        log_type = []
        log_type_info and log_type.append(LogType.Info.value)
        log_type_alert and log_type.append(LogType.Alert.value)
        log_type_error and log_type.append(LogType.Error.value)
        log_type_warning and log_type.append(LogType.Warning.value)
        db = ctx.db
        with db.cursor() as cur:
            sql = f"""
select top ? TimeLogged , %External(Type) Type, ConfigName, Text
from Ens_Util.Log
where
{"ConfigName = ?" if item_name else "1=1"}
{f"and type in ({', '.join(['?'] * len(log_type))})" if log_type else ""}
order by id desc
"""
            params = [limit, *([item_name] if item_name else []), *log_type]
            cur.execute(sql, params)
            for row in cur.fetchall():
                logs.append(f"{row[0]} {row[1]} {row[2]} {row[3]}")
        return "\n".join(logs)

    @server.tool(description="Get Interoperability Production queues")
    async def interoperability_production_queues(
        ctx: Context,
    ) -> str:
        queues = []
        db = ctx.db
        with db.cursor() as cur:
            sql = "select * from Ens.Queue_Enumerate()"
            cur.execute(sql)
            rows = cur.fetchall()
            queues = [", ".join([f"{cell}" for cell in row]) for row in rows]
        return "\n".join(queues)
