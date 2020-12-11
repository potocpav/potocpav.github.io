---
layout: post
title:  "Precise Typing Implies Functional Programming"
date:   2020-12-12 14:30:00 +0100
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

<p style="font-weight: bold; font-size: larger; padding: 0.5rem; margin: 1rem; border: 1px solid black; text-align: center;">
Functional programming is the consequence of using types to precisely encode program semantics.
</p>

If you agree that type systems should be used to their full potential, functional programming is not much of a paradigm - it is rather just a natural consequence. And it is quite uncontroversial to see that type systems should be wielded efficiently to prevent bugs and maximize correctness. That's, after all, precisely what they were designed to do in the first place.

Note that the above statement is an implication:

$$\text{precise types} ⇒ \text{functional programming}.$$

The converse isn't true, as FP is also possible in weakly-typed languages:

$$\text{functional programming} ⇏ \text{precise types}.$$

<!-- Indeed, one can arrive at functional programming from multiple directions, as is the case with many other good ideas. -->

Given that the value of precise typing is self-evident, I will focus on arguing that FP indeed follows from precise typing in the following sections.

## Types of Values

Types define (among other things) the set of all possible values a variable can take. Precise types constrain variables to only semantically valid values. Types should, ideally, contain no semantically invalid values.

Consider, for example, nullable types. They are convenient to have, and many languages make them nearly universal. But this universality brings impreciseness. While nullable types are useful for returning *from* functions, they are mostly wrong for passing *into* functions. Every function has to correctly handle each of its arguments possibly being null, and failure to do so often results in `NullPointerException` or equivalent. You have to correctly propagate through your program an extra failure condition for each variable whether it makes sense or not.

We can get rid of this problem by making only some types nullable, perhaps using an `Optional<Type>`.

Similar considerations arise for values which may be one of multiple things. An example may be  modeling remote data which must be fetched from a server. Remote data may be in multiple mutually-exclusive states:

* Data was not yet requested.
* Data was requested, but we did not get a response yet.
* There was an error on request.
* Data was successfully fetched.

This can be perfectly captured as an algebraic data type (ADT), for example, in Haskell:

```haskell
data RemoteData err res
  = NotAsked
  | Loading
  | Failure err
  | Success res
```

There are no extra values here, and every `RemoteData` variable you construct is guaranteed to be valid. You could simulate `RemoteData` without ADTs, but it would always contain invalid values. Those could be hidden inside a module/class with a safe interface, but this just shifts responsibility to the class implementation. Here is [a great article](https://lexi-lambda.github.io/blog/2020/11/01/names-are-not-type-safety/) detailing why this approach is suboptimal.

In conclusion, algebraic data types, one of the characteristics of FP style, are needed to precisely model value semantics.

## Functions

Next, let's look at functions. Most languages specify the means by which a function can interact with the rest of the program via **function signature**, consisting of **argument types** and the **return type**. Argument types specify the prerequisites, and the return type specifies the effects (results) of the function.

However, arguments and the return value don't specify function interface precisely. Functions can also do various side-effects not captured by the signature. They can:

* Access global variables, static variables, or instance variables
* Access external resources, such as PRNG state, network state, file IO, console, etc.
* Mutate arguments
* Throw exceptions

These are interactions that must be well documented and kept in mind by the programmers. They may create long-range order dependencies, which the type system doesn't know about. If side effects are not used sparingly, function signatures are not very descriptive.

We can increase type precision by getting rid of these escape hatches. Without them, function results are observable only through the return value, and the function can't access anything but its arguments. This makes type signatures much more expressive. Functions like this are called **pure**, and they are used pervasively in FP style.

Limiting ourselves to only pure functions may seem very... limiting. Obviously, side-effects exist because they are practical. How can we hope to do anything useful using just pure functions? Without diving deeper into this topic, rest assured that people write programs in languages with *only* pure functions, and it works just fine. The drawback is the steep learning curve, but it is only an upfront cost, paid once in a lifetime.

Purely functional IO requires pervasive use of higher-order functions, which is another FP characteristic.

### Mutability

If we limit ourselves to only pure functions, mutability is no longer very useful. Functions can't access anything but their arguments, and those can't be modified. This means that mutability is confined only to function bodies, where it can serve as a convenience. Some languages use function calls instead of `for` and `while` loops, which supersedes the few remaining use-cases for mutable values.

## Patterns

Now we have precise value and function types, but that is not enough. We also need a way to specify relations between them. Consider, for example, a sorting algorithm. It consists of a function `sort` together with a less-or-equal operator `leq`:

```rust
sort(Array<T>) -> Array<T>
leq(T, T) -> Bool // less or equal, ≤
```

The correctness of `sort` depends crucially on the semantics of `leq`: it can't be any old function, it must be a [total order](https://en.wikipedia.org/wiki/Total_order). It must satisfy the following relations:

* Antisymmetry. If `a ≤ b` and `b ≤ a` then `a = b`.
* Transitivity. If `a ≤ b` and `b ≤ c` then `a ≤ c`.
* Connexity. `a ≤ b` or `b ≤ a`.

If some of these are not satisfied, `sort` behaviour may not be what we expect:

```python
>>> sorted([4, float('nan'), 2, 1])
[4, nan, 1, 2]
```

This result is clearly incorrect, and it is because the `leq` is not a total order over IEEE 754 floats; it doesn't satisfy connexity. We need a way to encode this requirement into the type system, otherwise these kinds of bugs can't be prevented. This is what typeclasses/traits are used for. In Haskell:

```haskell
sort :: Ord a => [a] -> [a]
```

The `Ord` constraint tells us that we have an `≤` which forms a total order over `a`. In Rust, there is an equivalent pattern, this time in-place:

```rust
impl<T> Vec<T> {
    pub fn sort(&mut self) where T: Ord,
}
```

And indeed, `Ord` is not implemented for floats, which prevents the patological case above. Users of `sort` and orderable types can rest assured that they can't mess up the composition.

For a different example, suppose we want to make a parralel array sum function. This function splits the array into N sub-arrays, sums up each one in a thread, and finally sums the sub-results together. To get the same result regardless of the number of sub-arrays, our sum operation must be associative. We can express this by using the `Semigroup a` constraint which provides us with an associative operation over `a`.

```haskell
parallelSum :: Semigroup a => [a] -> a
```

This pattern of having lawful structures is ubiquitous in functional programming, and there are many well-known algebraic structures. In OOP languages, interfaces or classes could be used to the same effect, however, they have [many restrictions](https://stackoverflow.com/a/8123973) which make them much less useful.

## Other Options

We could achieve some of our goals by using other language features, not just types. For example, nullable types are sometimes a language primitive (Kotlin, Swift, SQL). Errors can be signalized using exceptions instead of return types (Java, C++). I would argue that both of these approaches are simultaneously more complex and less powerful than a type-based system. I will not go in depth on this topic, however, since this article is long enough as it is.

Mutable output arguments can be used in addition to return values. I don't see any problem with this alternative, as long as these arguments are explicitly marked.

## Notes on OOP

Object oriented programming encourages both imprecise data types, and non-descriptive functional signatures.

**Imprecise data types** arise because classes frequently contain **many** fields. This is caused by:

* OOP mental model of (thing == instance) is often not granular enough.
* Uninitialized states [are sometimes unavoidable](https://250bpm.com/blog:4/).
* References to other classes bring in their fields too.
* Nullability pervasiveness in mainstream OOP languages.
* Inheritance brings unnecessary baggage.

Often, tons invalid states are possible in classes. Keeping state consistent is a **major** challenge.

**Non-descriptive functional signatures** are given by the fact that functions have blanket access to instance variables. This is the same as passing in a bunch of mostly unnecessary arguments, which goes against descriptive function types. Worse, functions may work mainly through instance state manipulation instead of through return values. This leads to non-descriptive types, and by trying to compensate, to overly descriptive names. Ever seen code like this?

```java
private void includeSetupAndTeardownPages() throws Exception {
    includeSetupPages();
    includePageContent();
    includeTeardownPages();
    updatePageContent();
}

private void includeSetupPages() throws Exception {
    if (isSuite)
      includeSuiteSetupPage();
    includeSetupPage();
}

private void includeSuiteSetupPage() throws Exception {
    include(SuiteResponder.SUITE_SETUP_NAME, "-setup");
}

private void includeSetupPage() throws Exception {
    include("SetUp", "-setup");
}
```

Notice how function signatures are devoid of any information - every function has the exact same signature! Any of the statements can be duplicated, omitted, or rearranged without the compiler complaining. Control flow is fully implicit and the type system is all but useless. Luckily, this hardcore OOP style [is on the decline](https://qntm.org/clean).

In a purely functional setting, this can't happen. Any pure function which returns `void` is useless since it conveys no information in its return value. As a rule of thumb, even in non purely functional setting, `void`-returning functions should rarely be used.

## Conclusion

We have seen how the characteristics of functional programming arise from insisting on descriptive types. Using the type system to its full potential decreases the number of bugs and allows one write code much more confidently.

The main take-away is that functional programming does one thing better than other approaches: type system utilization. This doesn't mean that FP is overall better for software development. Perhaps in the process of being pedantic with types we arrived at a paradigm that is too impractical for everyday use.

Showing that this is not the case, and showing how effectful systems can be written in a purely functional style may be the topic of a future blog post.


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

## See Also

* [[83d4b42b|OOP Deconstruction]]
* [[79be9c2a|OOP Notes]]
