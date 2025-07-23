#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 24, 2025
"""
from __future__ import annotations

from collections.abc import Callable, Awaitable
from typing import TypedDict, TypeVar, Any, cast
from typing_extensions import ParamSpec, Concatenate
from langgraph.checkpoint.memory import InMemorySaver

from functools import wraps
from langgraph.func import task as _task, entrypoint as _entrypoint, TaskFunction
from langchain_core.runnables import RunnableConfig, Runnable

# ----------------- typing primitives -----------------
S = TypeVar("S")  # your class (self)
P = ParamSpec("P")  # params of the original method (excluding self)
R = TypeVar("R", covariant=True)  # return type
I = TypeVar("I")  # entry payload type
O = TypeVar("O")  # entry output type

_Method = Callable[Concatenate[S, P], R]
_MethodA = Callable[Concatenate[S, P], Awaitable[R]]
_Entry = Callable[[S, I, RunnableConfig], O]
_EntryA = Callable[[S, I, RunnableConfig], Awaitable[O]]


# ----------------- decorators -----------------
def method_task(
    __func_or_none__: _Method[S, P, R] | _MethodA[S, P, R] | None = None,
    *,
    config_key: str = "self",
    **kwargs: Any
) -> Callable[[_Method[S, P, R] | _MethodA[S, P, R]], TaskFunction[P, R]] \
     | TaskFunction[P, R]:
    """
    Decorator to turn an *instance method* into a langgraph.func.task.
    self is fetched from config["configurable"][config_key].
    """

    def _decorate(fn: _Method[S, P, R] | _MethodA[S, P, R]) -> TaskFunction[P, R]:
        @wraps(fn)
        def adapted(*args: P.args, config: RunnableConfig, **kw: P.kwargs):
            self_obj = cast(S, config["configurable"][config_key])
            return fn(self_obj, *args, config, **kw)

        # Use the real @task to get a TaskFunction back, then cast its generics to ours.
        tf = _task(**kwargs)(adapted)

        return cast(TaskFunction[P, R], tf)

    # Support both decorator styles: @method_task(...) and @method_task without parens
    if __func_or_none__ is not None:
        return _decorate(__func_or_none__)

    return _decorate


def method_entrypoint(
    *, config_key: str = "self", **ep_kwargs: Any
) -> Callable[[_Entry[S, I, O] | _EntryA[S, I, O]], Runnable[I, O]]:
    """
    Decorator to turn an *instance method* into a langgraph.func.entrypoint.
    The wrapped method signature should be: (self, payload: I, *, config: RunnableConfig) -> O
    """

    def deco(fn: _Entry[S, I, O] | _EntryA[S, I, O]):
        @wraps(fn)
        def adapted(payload: I, *, config: RunnableConfig) -> O | Awaitable[O]:
            self_obj = cast(S, config["configurable"][config_key])
            return fn(self_obj, payload, config=config)

        return cast(Runnable[I, O], _entrypoint(**ep_kwargs)(adapted))

    return deco


class In(TypedDict):
    sql: str


class Out(TypedDict):
    rows: list[dict]


class Service:
    def __init__(self, db):
        self.db = db

    @method_task()
    def run_query(self, sql: str, config):
        # use self like a normal method
        rows = self.db.execute(sql)
        return list(rows)

    @method_entrypoint(checkpointer=InMemorySaver())
    def main(self, payload: In, *, config) -> Out:
        rows = self.run_query(payload["sql"]).result()
        return {"rows": rows}


# ---- run it ---------------------------------------------------------------
if __name__ == '__main__':

    class MockDBSession:
        def execute(self, sql: str):
            # Mock database execution
            print(f"Executing SQL: {sql}")
            return [{"n": 1}]  # Mock result


    svc = Service(MockDBSession())

    cfg = {
        "configurable": {
            "thread_id": "u-42",   # needed for persistence
            "self": svc,           # <— inject the instance
        }
    }
    out = svc.main.invoke({"sql": "SELECT 1 AS n"}, cfg)
    print(out)
