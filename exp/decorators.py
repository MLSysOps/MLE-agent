#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 24, 2025
"""
from __future__ import annotations

import inspect
from collections.abc import Callable, Awaitable
from inspect import Parameter, Signature
from typing import TypeVar, Any, cast, TYPE_CHECKING
from typing_extensions import ParamSpec, Concatenate

from langgraph.func import task as _task, entrypoint as _entrypoint, TaskFunction
from langchain_core.runnables import RunnableConfig

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

if TYPE_CHECKING:
    from typing import Sequence, Unpack, overload

    from langgraph._typing import DeprecatedKwargs
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.store.base import BaseStore
    from langgraph.cache.base import BaseCache
    from langgraph.types import CachePolicy, RetryPolicy, StreamWriter


# ------------------ helpers ------------------
def _wants(name: str, fn: Callable[..., Any]) -> bool:
    return name in inspect.signature(fn).parameters


def _kwargs_for_user_fn(
    fn: Callable[..., Any],
    *,
    config: "RunnableConfig",
    store: "BaseStore | None",
    writer: "StreamWriter | None",
    previous: Any,
) -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if _wants("config", fn):
        kw["config"] = config
    if _wants("store", fn):
        kw["store"] = store
    if _wants("writer", fn):
        kw["writer"] = writer
    if _wants("previous", fn):
        kw["previous"] = previous
    return kw


def _copy_meta(dst: Callable[..., Any], src: Callable[..., Any]) -> None:
    """Copy a few attrs WITHOUT creating __wrapped__ (which would break signature)."""
    for attr in ("__name__", "__qualname__", "__doc__", "__module__"):
        try:
            setattr(dst, attr, getattr(src, attr))
        except Exception:
            pass

def _task_signature_of(fn: Callable[..., Any]) -> Signature:
    """
    Build a signature that:
    - Drops `self`
    - Keeps all original user params
    - Adds a kw-only `config` param (optional) so LangGraph can inject it
    """
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())

    # drop self if present
    if params and params[0].name == "self":
        params = params[1:]

    # add kw-only config (optional)
    params.append(Parameter("config", kind=Parameter.KEYWORD_ONLY, default=None))
    sig.replace(parameters=params, return_annotation=sig.return_annotation)
    return sig


# ----------------- decorators -----------------
def method_task(
    __func_or_none__: _Method[S, P, R] | _MethodA[S, P, R] | None = None,
    *,
    config_key: str = "self",
    name: str | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    cache_policy: CachePolicy[Callable[P, str | bytes]] | None = None,
    **kwargs: Unpack[DeprecatedKwargs],
) -> Callable[[_Method[S, P, R] | _MethodA[S, P, R]], TaskFunction[P, R]] \
     | TaskFunction[P, R]:
    """
    Decorator to turn an *instance method* into a langgraph.func.task.
    self is fetched from config["configurable"][config_key].
    """

    def _decorate(fn: _Method[S, P, R] | _MethodA[S, P, R]) -> TaskFunction[P, R]:
        wants_config = _wants("config", fn)

        def adapted(*args: P.args, config: RunnableConfig, **kw: P.kwargs):
            self_obj = cast(S, config["configurable"][config_key])
            if wants_config:
                return fn(self_obj, *args, config, **kw)
            else:
                return fn(self_obj, *args, **kw)

        _copy_meta(adapted, fn)
        _task_signature_of(adapted)

        # Use the real @task to get a TaskFunction back, then cast its generics to ours.
        # noinspection PyArgumentList
        tf = _task(
            name=name,
            retry_policy=retry_policy,
            cache_policy=cache_policy,
            **kwargs,  # type: ignore[arg-type]
        )(adapted)

        return cast(TaskFunction[P, R], tf)

    # Support both decorator styles: @method_task(...) and @method_task without parens
    if __func_or_none__ is not None:
        return _decorate(__func_or_none__)

    return _decorate


# noinspection PyPep8Naming
class method_entrypoint:  # noqa: N801
    """
    Class-method friendly wrapper around `langgraph.func.entrypoint`.

    - Injects `self` from `config["configurable"][config_key]`
    - Forwards only the injectable params actually requested by your method
      (`config`, `store`, `writer`, `previous`).
    - Returns a `Runnable[I, O]` so it's accepted by `StateGraph.add_node`.
    """

    def __init__(
        self,
        *,
        checkpointer: "BaseCheckpointSaver | None" = None,
        store: "BaseStore | None" = None,
        cache: "BaseCache | None" = None,
        config_schema: "type[Any] | None" = None,
        cache_policy: "CachePolicy | None" = None,
        retry_policy: "RetryPolicy | Sequence[RetryPolicy] | None" = None,
        config_key: str = "self",
        **kwargs: "Unpack[DeprecatedKwargs]",
    ) -> None:
        self._config_key = config_key
        self._inner = _entrypoint(
            checkpointer=checkpointer,
            store=store,
            cache=cache,
            config_schema=config_schema,
            cache_policy=cache_policy,
            retry_policy=retry_policy,
            **kwargs,
        )

    def __call__(self, fn: Callable[..., Any]):
        # First param (after self) is the workflow input
        # We keep our adapter's signature compatible with entrypoint:
        #   payload, *, store, writer, config, previous
        # so that get_runnable_for_entrypoint() can inject them.
        def adapted(
            payload: I,
            *,
            config: RunnableConfig,
            store: BaseStore | None = None,
            writer: StreamWriter | None = None,
            previous: Any = None,
        ) -> O | _entrypoint.final[Any, Any]:
            # Recover self from config
            self_obj = cast(S, config["configurable"][self._config_key])

            # Build kwargs only for what the user method declared
            kw = _kwargs_for_user_fn(
                fn,
                config=config,
                store=store,
                writer=writer,
                previous=previous,
            )
            return fn(self_obj, payload, **kw)

        # Copy meta attrs from the original function to the adapted one
        _copy_meta(adapted, fn)

        return self._inner(adapted)
