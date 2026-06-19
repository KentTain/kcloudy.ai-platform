"""包含 snapshot 方法定义的模块."""

from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.storage import PipelineStorage


@verb(name="snapshot")
async def snapshot(
    input: VerbInput,
    name: str,
    formats: list[str],
    storage: PipelineStorage,
    **_kwargs: dict,
) -> TableContainer:
    """对表格数据进行完整快照."""
    data = input.get_input()

    for fmt in formats:
        if fmt == "parquet":
            await storage.set(name + ".parquet", data.to_parquet())
        elif fmt == "json":
            await storage.set(
                name + ".json",
                data.to_json(orient="records", lines=True, force_ascii=False),
            )

    return TableContainer(table=data)
