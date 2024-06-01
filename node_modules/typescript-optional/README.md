# TypeScript Optional

[![npm](https://img.shields.io/npm/v/typescript-optional.svg)](https://www.npmjs.com/package/typescript-optional)
[![License](https://img.shields.io/npm/l/typescript-optional.svg)](https://www.npmjs.com/package/typescript-optional)

[![codecov](https://codecov.io/gh/bromne/typescript-optional/branch/master/graph/badge.svg?token=vwg9UEGoic)](https://codecov.io/gh/bromne/typescript-optional)

Optional (like Java) implementation in TypeScript

## Overview

`Optional<T>` is a type which *may* or *may not* contain a *payload* of type `T`.
It provides a common interface regardless of whether an instance is *present* or is *empty*. 

This module is inspired by [Optional class in Java 8+](https://docs.oracle.com/javase/10/docs/api/java/util/Optional.html).

 The following methods are currently not supported:
 
 - `equals`
 - `toString`
 - `hashCode`
 - `stream`

### Install

```
npm install --save typescript-optional
```

## Usage

### import

```ts
// import Optional type from this module
import { Optional } from "typescript-optional";
```

### creating `Optional<T>` objects

```ts
const nullableString: string | null = /* some nullable value */;

// all the following variables will be parameterized as Optional<string>.
const optional = Optional.ofNullable(nullableString);
const optionalPresent1 = Optional.ofNullable("foo");
const optionalPresent2 = Optional.ofNonNull("foo"); // accepts non-null value (or else throws TypeError)
const optionalEmpty1: Optional<string> = Optional.empty(); // type hinting required
const optionalEmpty2 = Optional.empty<string>(); // or parameterize explicitly
```

### operations

```ts
const optional: Optional<string> = Optional.ofNullable( /* some optional value: null | string */ );

// force to retrieve the payload. (or else throws TypeError.)
// this method is not used match.
optional.get();

// represent whether this is present or not.
optional.isPresent();

// represent whether this is empty or not. (negation of `isPresent` property)
optional.isEmpty();

// if a payload is present, execute the given `consumer`.
optional.ifPresent(value => console.log(value));

// if a payload is present, execute the first argument (`consumer`),
// otherwise execute the second argument (emptyAction).
optional.ifPresentOrElse(value => console.log(value), () => console.log("empty"));

// filter a payload with additional predicate.
optional.filter(value => value.length > 0);

// map a payload with the given mapper.
optional.map(value => value.length);

// map a payload with the given mapper which returns value wrapped with Optional type.
const powerIfPositive: (x: Number) => Optional<Number>
    = x => (x > 0) ? Optional.ofNonNull(x * x) : Optional.empty();
const numberOptional: Optional<null | number> = Optional.ofNullable(/* some optional value: null | number */)
numberOptional.flatMap(value => powerIfPositive(value as number));

// if this is present, return this, otherwise return the given another optional.
const another: Optional<string> = Optional.ofNullable(/* ... */);
optional.or(another);

// if this is present retrieve the payload,
// otherwise return the given value.
optional.orElse("bar");

// if a payload is present, retrieve the payload, 
// otherwise return a value supplied by the given function.
optional.orElseGet(() => "bar");

// if a payload is present, retrieve the payload,
// otherwise throw an exception supplied by the given function.
optional.orElseThrow(() => new Error());

// if a payload is present, retrieve the payload,
// otherwise return null.
optional.orNull();

// if a payload is present, retrieve the payload,
// otherwise return undefined.
optional.orUndefined();

// return an appropriate result by emulating pattern matching with the given cases.
optional.matches({
    present: value => value.length,
    empty: () => 0, 
})

// convert this to an Option value.
optional.toOption();
```

### prototype-free types

While `Optional`'s fluent interface for method chaining with `prototype` is usually useful and elegant,
relying on `prototype` can cause some problems in certain situations like that an external function copies such objects *except* `prototype`.
For example, `setState` of React reflects the given value as a state except the value's `prototype` (and then you will see "TypeError: undefined is not a function" in runtime though TypeScript compilation has been succeeded!).

To avoid this issue, you have three options that *convert* an `Optional` into a *prototype-free*, or a simple JavaScript object (associative array, string etc.).

- `Optional.orNull`
- `Optional.orUndefined`
- `Optional.toOption`

#### `Optional.orNull` and `Optional.orUndefined`

Using `Optional.orNull` or `Optional.orUndefined` is the simple way to obtain prototype-free objects.
These methods convert an `Optional<T>` into a value of *type union*.

`Optional<T>.orNull` returns `T | null`.

`Optional<T>.orUndefined` returns `T | undefined`. The `T | undefined` type is compatible with [optional parameters and properties](http://www.typescriptlang.org/docs/handbook/advanced-types.html#optional-parameters-and-properties) of TypeScript.

Use `Optional.ofNullable` to restore an Optional value from a value of these type unions.

```ts
const update: <T> (original: T) => T = /* some external function that returns without the prototype */
const optional: Optional<string> = /* some Optional object */;

let nullable: string | null = optional.orNull();
let orUndefined: string | undefined = optional.orUndefined();

// update using external functions!
nullable = update(nullable);
orUndefined = update(orUndefined);

// retore from (string | null).
const optionalFromNullable: Optional<string> = Optional.ofNullble(nullable);

// restore from (string | undefined).
const optionalFromOrUndefined: Optional<string> = Optional.ofNullble(orUndefined);
```

#### `Option.toOption`

As a more explicit way to obtain prototype-free objects, `Optional.toOption` is provided.
This method convert an `Optional<T>` into an object of `Option<T>` type, which conforms to [*discriminated unions*](http://www.typescriptlang.org/docs/handbook/advanced-types.html#discriminated-unions) also known as *algebraic data types*.
Refer the [API document](lib/types.ts) of `Option<T>` to learn about the structure.

```ts
const update: <T> (original: Option<T>) => T = /* some external function that returns without the prototype */
const optional: Optional<string> = /* some Optional value */;

let option: Option<string> = optional.toOption();

// update using external functions!
option = update(option);

// restore from Option<T>.
const optionalFromOption: Optional<string> = Optional.from(option);
```

## License

MIT License - [LICENSE.md](LICENSE.md)
