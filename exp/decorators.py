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
from typing import TypeVar, Any, cast, overload, TYPE_CHECKING
from weakref import WeakKeyDictionary

from langgraph.pregel import Pregel
from typing_extensions import ParamSpec, Concatenate

from langgraph.func import task as _task, entrypoint as _entrypoint, TaskFunction
from langchain_core.runnables import RunnableConfig

# ----------------- typing primitives -----------------
S = TypeVar("S")  # your class (self)
P = ParamSpec("P")  # params of the original method (excluding self)
T = TypeVar("T", covariant=True)  # return type
I = TypeVar("I")  # entry payload type
O = TypeVar("O")  # entry output type

_Entry = Callable[[S, I, RunnableConfig], O]
_EntryA = Callable[[S, I, RunnableConfig], Awaitable[O]]

if TYPE_CHECKING:
    from typing import Sequence, Unpack

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


@overload
def method_task(
    *,
    name: str | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    cache_policy: CachePolicy[Callable[P, str | bytes]] | None = None,
    **kwargs: Unpack[DeprecatedKwargs],
) -> Callable[
    [Callable[P, Awaitable[T]] | Callable[P, T]],
    TaskFunction[P, T],
]: ...


@overload
def method_task(
    __func_or_none__: Callable[P, Awaitable[T]] | Callable[P, T],
) -> TaskFunction[P, T]: ...


def method_task(
    __func_or_none__: Callable[P, Awaitable[T]] | Callable[P, T] | None = None,
    *,
    name: str | None = None,
    retry_policy: RetryPolicy | Sequence[RetryPolicy] | None = None,
    cache_policy: CachePolicy[Callable[P, str | bytes]] | None = None,
    **kwargs: Unpack[DeprecatedKwargs],
) -> (
    Callable[[Callable[P, Awaitable[T]] | Callable[P, T]], TaskFunction[P, T]]
    | TaskFunction[P, T]
):
    """
    Decorate an *instance method* into a `langgraph.func.task`.

    Typing behavior:
      - If decorating `def f(self, *args) -> R`, the attribute type becomes
        `TaskFunction[P, R]`, so `obj.f(...).result()` is typed as `R`.
    Runtime behavior:
      - Binds `self` via the descriptor (`__get__`), not via `config`.
      - Forwards `config` only if the method declared it.
      - Synthesizes an adapter signature: original params + optional kw-only `config`.
    """

    class _MethodTaskDescriptor:
        __slots__ = ("_fn", "_name", "_retry_policy", "_cache_policy", "_kwargs", "_cache")

        def __init__(self, fn: Callable[P, T]) -> None:
            self._fn = fn
            self._name = name
            self._retry_policy = retry_policy
            self._cache_policy = cache_policy
            self._kwargs = kwargs
            self._cache: "WeakKeyDictionary[object, TaskFunction[Any, Any]]" = WeakKeyDictionary()

        def __get__(
            self,
            obj: S | None,
            objtype: type[Any] | None = None,
        ) -> TaskFunction[P, T] | _MethodTaskDescriptor:
            if obj is None:
                return self

            cached = self._cache.get(obj)
            if cached is not None:
                return cast(TaskFunction[P, T], cached)

            fn = self._fn
            wants_cfg = _wants("config", fn)

            # Adapter that binds `self` and optionally passes through `config`
            def adapted(*args: P.args, **kw: P.kwargs):
                cfg = kw.pop("config", None)
                if wants_cfg:
                    kw["config"] = cfg
                # Bind the instance
                return cast(Callable[..., Any], fn)(obj, *args, **kw)

            # Avoid functools.wraps; set a synthetic signature LangGraph can see
            _copy_meta(adapted, fn)
            adapted.__signature__ = _task_signature_of(fn)  # type: ignore[attr-defined]

            # noinspection PyArgumentList
            tf = _task(
                name=self._name,
                retry_policy=self._retry_policy,
                cache_policy=self._cache_policy,
                **self._kwargs,
            )(adapted)

            self._cache[obj] = tf
            return cast(TaskFunction[P, T], tf)

    def _decorate(fn: Callable[P, T] | Callable[P, Awaitable[T]]):
        # Return the descriptor; the overloads above tell the checker that
        # the final attribute type is TaskFunction[P, R].
        return _MethodTaskDescriptor(fn)

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
        **kwargs: "Unpack[DeprecatedKwargs]",
    ) -> None:
        self._fn: Callable[..., Any] | None = None
        self._inner = _entrypoint(
            checkpointer=checkpointer,
            store=store,
            cache=cache,
            config_schema=config_schema,
            cache_policy=cache_policy,
            retry_policy=retry_policy,
            **kwargs,
        )
        self._cache: "WeakKeyDictionary[object, Pregel]" = WeakKeyDictionary()

    def __call__(self, fn: Callable[..., Any]):
        self._fn = fn
        return self

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._name_in_class = name

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[S] | None = None,
    ) -> "method_entrypoint":
        """
        If called on the class itself, return the decorator.
        """
        ...

    @overload
    def __get__(
        self,
        instance: S,
        owner: type[S] | None = None,
    ) -> Pregel[S, I, O]:
        """
        If called on an instance, return the runnable for that instance.
        """
        ...

    def __get__(self, obj: S | None, objtype: type[S] | None = None) -> Pregel[S, I, O] | "method_entrypoint":
        if obj is None:
            # If called on the class itself, return the decorator
            return self

        cached = self._cache.get(obj)
        if cached is not None:
            # If we already have a cached runnable for this class, return it
            return cast(Pregel[S, I, O], cached)

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
            # Build kwargs only for what the user method declared
            kw = _kwargs_for_user_fn(
                self._fn,
                config=config,
                store=store,
                writer=writer,
                previous=previous,
            )
            return self._fn(obj, payload, **kw)

        # Copy meta attrs from the original function to the adapted one
        _copy_meta(adapted, self._fn)
        pregel = self._inner(adapted)
        self._cache[obj] = pregel

        return pregel
