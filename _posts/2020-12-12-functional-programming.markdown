---
layout: post
title:  "Precise Typing Implies Functional Programming"
date:   2020-12-11 14:30:00 +0100
categories: programming
---
Functional programming (FP) is, similarly to other programming paradigms, quite difficult to pin down. Instead of having a clear definition, these characteristics are commonly associated with functional style:

* Functions are treated as first-class citizens. They are frequently passed as arguments to other functions.
* Immutable values are preferred over mutable values.
* Functions are pure. They are deterministic and side-effect-free, similarly to mathematical functions.
* Algebraic structures are used as abstractions.

Seeing the value of these characteristics is not easy, however. Each of them must be argued separately, and it can be difficult to make a solid case for their utility, especially to a person who is used to programming in a different paradigm. How can we convince fellow developers that all the functional weirdness is warranted? I will try to present an unified argument for all the FP characteristics in this article.

<!--
* Why should I use first-class functions rather than first-class objects?
* Isn't function composition unnecessarily cryptic in comparison to simple sequential statements?
* Purity is valuable, but aren't side-effects sometimes more natural?
-->

<!-- Functional programming arises in a number of ways. I will explore, how functional programming follows from strong typing. This illustrates nicely why various FP concepts are useful, as they help us leverage the type system in an optimal way. -->

It turns out that all of the above points can be derived from a single design rule.

<!-- There is an underlying characteristic hidden beneath the usual functional programming patterns. The characteristics above can be seen merely as effects of this characteristic, and its value is rather self-evident. Without further ado, here it is: -->

<style>
.banner {
    font-weight: bold;
    font-size: larger;
    padding: 0.5rem;
    margin: 1rem;
    border: 1px solid black;
    text-align: center;
}
</style>
<p style="font-weight: bold; font-size: larger; padding: 0.5rem; margin: 1rem; border: 1px solid black; text-align: center;" class="banner">
Functional programming is the consequence of using types to precisely encode program semantics.
</p>

If you agree that type systems should be used to their full potential, functional programming is not much of a paradigm - it is rather just a natural consequence. And it is quite uncontroversial to see that type systems should be wielded efficiently to prevent bugs and maximize correctness. That's, after all, precisely what they were designed to do in the first place.

Note that the above statement is an implication:

$$\text{precise types} ⇒ \text{functional programming}.$$

The converse isn't true, as FP is also possible in weakly-typed languages:

$$\text{functional programming} ⇏ \text{precise types}.$$

<!-- Indeed, one can arrive at functional programming from multiple directions, as is the case with many other good ideas. -->

Given that the value of precise typing is self-evident, I will focus on arguing that FP indeed follows from precise typing in the following sections. In the following sections, I will try to show how each of the signature FP features serves to make types more precise.

## Algebraic Data Types

Data types allow us to specify what values an expression might take. We want types to match semantics as precisely as possible. They would ideally allow all valid values while disallowing all invalid values. Algebraic data types (ADTs) provide us with a rich vocabulary to construct precise types in many scenarios.

For example, say we want to specify a type representing a JSON value.

```c++
// This is a JSON value.
JSON json;
```

What we don't want is a JSON value with a fine print attached:

```c++
// This is a JSON value¹
// ¹ or an inconsistent thing with undefined behavior on access
JSON json;
```

We can have a look at how this is done in practice. Here is how one might represent a JSON value in C++. Code is adapted and simplified from the popular [nlohmann's JSON library](https://github.com/nlohmann/json):

```c++
enum class value_t {
    null, boolean, number_float, integer, string, array, object,
};

union json_value {
    bool boolean;
    double number_float;
    std::int64_t number_integer;
    std::string *string;
    std::vector<json> *array;
    std::map<std::string, json> *object;
}

class json {
    value_t m_type;
    json_value m_value;
}
```

Consider what needs to be ensured for `json` to represent a valid JSON value:

* `m_type` must be an integer less than 7.
* `m_type` must correspond to the type of `m_value`.
* For a string, array, and object, `json_value` must be a valid pointer.
* Above points must be satisfied on all depth levels, since `json` is a tree structure.

These requirements are commonly known as **invariants**, and they are precisely the **rules that aren't captured by the type system**; they must be upheld by the programmer. Indeed, the `json` library [documents some of them in comments](https://github.com/nlohmann/json/blob/97fe455ad5dd889ed30cf23bc735bb038ef67435/include/nlohmann/json.hpp#L150-L155) and provides [functions to check their validity](https://github.com/nlohmann/json/blob/97fe455ad5dd889ed30cf23bc735bb038ef67435/include/nlohmann/json.hpp#L1227-L1233). To further facilitate safety, `m_type` and `m_value` are private, so only code internal to the JSON library must be careful about invariants.

This a compromise rather than the ideal case. We must trust the library internals to correctly uphold all the invariants. Nlohmann's JSON library contains more than 10,000 lines of code with access to the private fields of `json`, so this is definitely not a trivial concern!

Invariants arise from the inability of the type system. If we were able to construct a type which contains **only** valid JSON values, all these problems would disappear. We could expose data directly, since every value is valid by construction. There is no longer a trusted code-base, no assertions, tests or comments about invariants, we only need to trust the type-checker. Behold the Rust JSON representation, adapted from the canonical [serde library](https://github.com/serde-rs/json):

```rust
pub enum Json {
    Null,
    Bool(bool),
    Integer(i64),
    Float(f64),
    String(String),
    Array(Vec<Json>),
    Object(Map<String, Json>),
}
```

Rust `enum` is an union type which contains precisely one of the listed options:

* Either a `Null`,
* or a `Bool` with a single `bool` value,
* or an `Integer` with an `i64` value,
* etc.

Notice how the `Json` enum is public: there are no invariants. It is impossible to construct invalid values.

Rust enumerations are algebraic data types, and they enable us to model semantics much more precisely than plain structs. This shifts responsibility from the programmer to the type checker, and allows us to write more reliable software. Here I showed just one example, but surprisingly many different objects can be precisely described using ADTs.

To sum up, ADTs are a way to precisely model type semantics. Without proof^[1], I will assert that they are actually the **only** way: you need a construct of (at least) equivalent power to hope for precise types.This would mean that we have the first piece of the puzzle:

<p class="banner">
ADTs are the consequence of using types to precisely encode program semantics.
</p>



## Pure Functions

ToDo


## Algebraic Structures

ToDo

## Immutable Values

ToDo

## Higher-order Functions

ToDo

## Conclusion

We have seen how the characteristics of functional programming arise from insisting on descriptive types. Using the type system to its full potential decreases the number of bugs and allows one write code much more confidently.

The main take-away is that functional programming does one thing better than other approaches: type system utilization. This doesn't mean that FP is overall better for software development. Perhaps in the process of being pedantic with types we arrived at a paradigm that is too impractical for everyday use.

Showing that this is not the case, and showing how effectful systems can be written in a purely functional style may be the topic of a future blog post.

[^2] If I'm wrong on this, please point it out in the comments.

<!-- We will not consider argument names and function name as parts of function signature - their correspondence to semantics can't be checked by the compiler. Let me write down an example in C++:

```c++
int f(string a);
```

I replaced the names with placeholder letters since they are not a part of the signature. We can test how precise our types are by trying to guess what the function does and how it can be used. Here are some possibilities:

* `f` counts the number of bytes in `a`.
* `f` parses a `string` into an `int`. It throws an exception if `string` contains non-digit characters.
* `f` opens a file `a`, and returns file size. It throws if the file doesn't exist.
* `f` replaces all the non-ASCII characters in `a` with placeholders. It returns the number of replacements. -->
<!--
We can see that function signature is only a part of the function interface. Functions can do **so much more** than just returning a value. Based on function signature alone, we can't tell whether a function is doing any funny business under our feet, or how to correctly use it. Can we memoize the function? Can we safely call the function twice in parallel? Do we need to conjure up any external environment if we want to use the function in a different project? This information is not represented in the function signature. We have to inspect the innards, and the type checker can't prove that our analysis is correct.

Let's try to increase the precision of function signatures. We already have all the parts we need: a way to specify prerequisites (argument types), and a way to specify effects (return type). We just need to make these the **only** prerequisited and effects - get rid of escape hatches. We need to make our functions pure.

Pure functions are very pleasant to work with. They depend only on their arguments so they are easily tested and reasoned about. Their effects are constrained to the return value, so their execution is otherwise unobservable. Independent functions can be parallelized, re-ordered, or executed at arbitrary times without changing semantics. Flow of information (or lack thereof) is reified as argument passing.

## Methods and OOP

Class methods^[also known as instance functions], often suffer from very non-descriptive signatures, but the problem is opposite to what we saw before. Instead of failing to specify some prerequisites as arguments, they specify *more than they need*. Methods can access all the instance variables. This gives them a large surface they can work on, which often leads to non-obvious information flow, where the principal function effects are not their return values, but rather mutations of object state. With large objects, the number of possible states grow exponentially, and the probability that all of them are handled correctly by all functions is low.

TODO: example of an OOP interface which is hard to follow. Perhaps from Clean Code, or something.

## Values

For our intents and purposes, values are just entities that can be passed to and returned from functions. To pin down function semantics precisely, values need to be precise too. Ideally, they would specify what can be passed into a function or returned from one as tightly as possible.

* Tightly specifying arguments minimizes the number of values that the function needs to correctly handle
* Tightly specifying return values ensures that downstream functions don't need to correctly handle as many values.

Consider languages in which variables can be `null`. For each function argument, there is an extra `null` that needs to be considered, even if there is no valid action that can be taken for such an argument. Specifying only some values as nullable, for example using `optional<T>`, allows for tighter specifications.

If exceptions can be thrown from all functions, then non-throwing functions can't be marked as such. It may be better to use checked exceptions, or to use algebraic data types to explicitly mark functions which can fail, such as Rust's `Result<Ok, Err>`.

If the principle of tight value types is taken seriously, it may even lead to all functions being infallible, as is the case with Elm or PureScript. In these languages, there are no runtime exceptions, with some caveats. The compiler checks that all possible values are handled by each function.

<!--
To sum up, function prereqisites are arguments *and some other stuff.* Function effects are the return value *and some other stuff.* If we want to make the type system capture function semantics precisely, we must get rid of the escape hatches: either by convention, or by language restrictions. We move towards the functional programming approach of pure functions and no side-effects.
 -->
<!--
 ## Patterns

 Capturing the interfaces of groups of functions, rather than single functions.

 Typeclasses, sets, lattices, monoids, etc.

 map, filter, reduce

## Making Function Signatures Precise

Functional programming allows you to.

Is it practical? Haskell does that. People write software in Haskell. QED.

Is it more work? Yes, there is much more lifting going on. Stuff gets more abstract. But this is an upfront cost - a steeper learning curve.

What do we win? Since functions are pure, we get order independence. We can freely rearrange them, as long as there are no dependencies.


## Types

We used types in the previous paragraphs to constrain public interface of functions. We will now look at how types can be used to model function semantics as precisely as possible.

For data structures, honesty with types implies tight domain modelling. Facts about data should be encoded in types as precisely as possible. This implies:

- making invalid states unrepresentable



## Where to stop?

Designing software functionally is extra effort compared to imperative programming. Religiously following the FP paradigm may have diminishing returns, which would mean that there is a point where the extra effort is no longer justified by the benefits. Is there such a point?

The extra effort manifests in three ways:

1. Learing curve. It is hard to learn functional paradigm's more exotic patterns. This is the cost a developer pays only once in their life. Also known as "becoming a better programmer".
2. Planning. Modelling domains precisely with types requires some upfront planning. You may have to sit down with a pen and paper and try to understand your task as well as possible before you start writing code.
3. Day-to-day programming overhead. This is probably negligible.

Perhaps unintuitively, pinning your domain down with precise types doesn't decrease flexibility. Rather, types allow you to encode the requirements of your functions, but nothing extra. Functional code can be amazingly expressive. -->