# task-keeper

개인 할 일을 관리하는 작은 웹 API입니다. 책 3장의 스킬 실습용 예제 저장소입니다.

- 스택: Python, FastAPI, SQLAlchemy, SQLite
- 패키지 관리: uv
- 기본 브랜치: main

## 구조

```
task-keeper/
├── app/
│   ├── main.py              # FastAPI 앱과 엔드포인트
│   ├── database.py          # 엔진, 세션, Base
│   ├── models.py            # Task, Tag (다대다)
│   ├── schemas.py           # 응답/요청 스키마
│   └── services/
│       └── task_service.py  # list_tasks()의 태그 일괄 로딩
├── scripts/
│   └── seed.py              # 데모 데이터 생성
├── tests/
│   ├── conftest.py          # 메모리 DB, 테스트 클라이언트
│   ├── test_smoke.py        # 기본 동작 확인
│   └── test_task_queries.py # 직렬화를 포함한 SELECT 수 검증
├── pyproject.toml          # 의존성과 프로젝트 메타데이터
└── uv.lock                 # 잠금 파일
```

## 실행

uv가 설치돼 있어야 합니다. 없으면 https://docs.astral.sh/uv/ 를 보고 설치하세요.

```
uv sync                              # 의존성 설치 + 가상환경 생성
uv run python scripts/seed.py        # 데모 할 일 100개 생성
uv run uvicorn app.main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs
- 목록 조회: http://127.0.0.1:8000/tasks

## 엔드포인트

- `GET /tasks` 할 일 목록
- `POST /tasks` 할 일 생성. 본문 예: `{"title": "장보기", "tags": ["개인", "쇼핑"]}`
- `GET /tasks/{id}` 단건 조회

## 해결된 버그: 목록 조회 N+1

기존 `list_tasks()`는 응답 직렬화 과정에서 각 할 일의 태그를 따로 조회해, 할 일이 N개면 SELECT가 총 N+1회 실행됐습니다.

현재는 `selectinload(Task.tags)`로 태그를 일괄 로딩합니다. 할 일이 0개면 SELECT 1회, 1개와 10개면 각각 2회 실행됩니다. 대량 조회 시에는 SQLAlchemy가 태그 로딩을 여러 배치로 나눌 수 있습니다.

```python
from sqlalchemy.orm import selectinload

tasks = db.query(Task).options(selectinload(Task.tags)).all()
```

회귀 테스트는 할 일 0·1·10개를 준비한 뒤 새 세션에서 조회하고 응답을 직렬화하며, SELECT 수와 응답 내용을 검증합니다.

```
uv run pytest tests/test_task_queries.py -q
```

실제 쿼리는 아래 명령으로 서버를 실행한 뒤 `GET /tasks`를 호출해 콘솔에서 확인할 수 있습니다.

```
SQLALCHEMY_ECHO=1 uv run uvicorn app.main:app
```

이 변경이 책 3.8 실습의 작업 내용입니다. 이슈 생성부터 커밋, PR, 리뷰, 리뷰 반영까지 다섯 스킬로 처리합니다.

## 테스트

```
uv run pytest
```
