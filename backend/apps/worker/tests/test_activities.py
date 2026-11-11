from temporalio.testing import ActivityEnvironment

from driftless_core.schema import Catalog, Column, DataType, PrimaryKey, Table, TypeKind
from driftless_worker.activities import AssessInput, assess_catalog
from driftless_worker.workflows import ALL_WORKFLOWS, MigrationWorkflow


def _catalog(with_pk: bool) -> Catalog:
    table = Table(
        name="orders",
        columns=(Column(name="id", type=DataType.of(TypeKind.BIGINT), nullable=False),),
        primary_key=PrimaryKey(columns=("id",)) if with_pk else None,
    )
    return Catalog(engine="mysql", tables=(table,))


async def test_assess_activity_ready_when_no_blockers() -> None:
    env = ActivityEnvironment()
    out = await env.run(
        assess_catalog, AssessInput(catalog=_catalog(True), target_engine="postgres")
    )
    assert out.ready
    assert out.blocking == 0


async def test_assess_activity_reports_blockers() -> None:
    env = ActivityEnvironment()
    out = await env.run(
        assess_catalog, AssessInput(catalog=_catalog(False), target_engine="postgres")
    )
    assert not out.ready
    assert out.blocking == 1


def test_workflow_is_registered() -> None:
    assert MigrationWorkflow in ALL_WORKFLOWS
