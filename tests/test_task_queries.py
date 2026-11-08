import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models import Tag, Task
from app.schemas import TaskOut
from app.services.task_service import list_tasks


@pytest.mark.parametrize("task_count, expected_selects", [(0, 1), (1, 2), (10, 2)])
def test_list_tasks_query_count(db_session, task_count, expected_selects):
    db_session.add_all(
        Task(title=f"할 일 {index}", tags=[Tag(name=f"태그 {index}")])
        for index in range(task_count)
    )
    db_session.commit()
    engine = db_session.get_bind()
    selects = []

    def count_selects(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    # 준비 세션의 identity map이 지연 로딩 쿼리를 가리지 않도록 새 세션을 씁니다.
    event.listen(engine, "before_cursor_execute", count_selects)
    try:
        with Session(engine) as session:
            payload = [
                TaskOut.model_validate(task).model_dump(mode="json")
                for task in list_tasks(session)
            ]
    finally:
        event.remove(engine, "before_cursor_execute", count_selects)

    assert len(payload) == task_count
    assert {task["title"] for task in payload} == {
        f"할 일 {index}" for index in range(task_count)
    }
    assert {tag["name"] for task in payload for tag in task["tags"]} == {
        f"태그 {index}" for index in range(task_count)
    }
    assert len(selects) == expected_selects
