---
layout: post
title:  "Why GUI Programming Sucks, and How to Make it Better"
date:   2020-05-01 16:30:00 +0200
categories: programming
---

Designing UI libraries is hard. System integration, accessibility, styling, those are difficult to do properly. But this article is about something much harder. Designing a good UI from the developer's point of view.

Here is a fact of life: **developers hate writing user interfaces**. For good reasons: it is difficult, time-consuming and boring. That's why most personal projects are text-based, even though a GUI would perhaps be a better fit. Is UI programming really that difficult? Or do our UI frameworks simply suck?

In this article, I will argue that the latter is true: it's not inherently difficult to write UIs. If you have the right toolset, that is. I will dive into the design process behind such a toolset, **Concur**. Concur enables you to write complex applications, as well as write quick throw-away GUI scripts, in much the same way you would write console scripts in Python. With Concur, simple applications can be written just in a few lines of code, and complex applications are just as difficult as they need to be, not more.

## Problem Analysis

To understand how to create an UI framework, we need to carefully analyze the problem first.

User interfaces can be decomposed into atomic building blocks, **widgets** (aka **elements**, **controls**, **components**, etc.) They are your button, text box, window, etc. These widgets are composed to form more complex components, which in turn form the whole application. This *widget composition** is where the complexity lies, and what makes UI programming hard. Widgets are not just functions, or data structures - we can compose these quite easily. Widgets contain state, but they can also be interacted with, and fire events. Composing them in the right way is not a trivial problem.

To tackle widget composition, we must first understand it it detail. There are actually two distinct types of composition: composition in space, and composition in time.

**Composition in space** is the one mentioned above, and the one we commonly think of when we say "composition". We simply use it to display several widgets simultaneously. Composition in space has received much love from UI frameworks. It is tedious to do in code, so we have designer tools, even whole languages dedicated to composition in space.

**Composition in time** is much less obvious. Conceptually, it is about displaying or modifying a widget in reaction to interaction with another widget. Often, we need to change the widget tree dynamically: in installation wizards, multi-page forms, mode-based applications, etc. But it is much more common than that - perhaps we just need to enable/disable a text-box in reaction to some events. This can be also viewed as composition in time.

In other words:

**Composition in space** - widget A exists simultaneously with widget B. There is no inherent order of definition, or dependency.

**Composition in time** - future widgets depend on interaction with past widgets. There is an enforced order: we can't create future widgets until we know the results of interaction with past widgets.

This is what [traditional](https://www.qt.io/) [UI](https://www.gtk.org/) [frameworks](https://en.wikipedia.org/wiki/Windows_Forms) get wrong. They focus solely on composition in space, and leave composition in time implicit. But composition in time is the hard one; when not properly dealt with, it quickly leads to spaghetti. Widgets are mutated from random event handlers, state is ad-hoc and managed all over the place, edge cases proliferate.

## Solution

What is the solution then? As with most complex things, we need to analyze and decompose the problem, boil it to its essence, and then assemble the parts back together in a superior way.

Widgets [complect](https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/SimpleMadeEasy.md) (interleave, entwine, braid) state and behavior. To make our job easier, we need to untangle them. Since we will later make composition in time painless, we can take the [virtual DOM](https://en.wikipedia.org/wiki/React_(web_framework)#Virtual_DOM) approach and obliterate state altogether. That is, **widgets can't be mutated**, they can only be created anew, differently. Our widgets will be quite short-lived. We can go a small step further: **widgets only fire one event, ever**. If you need multiple events, just re-create the widget. We are already doing that for every state change anyway.

This may seem radical, but bear with me. It actually brings nice separation of concerns. Widgets just do widget stuff, look nice, and wait for an interaction. They delegate all the time-related issues to the primitives dealing with composition in time. Layout-related issues are likewise delegated to space composition primitives. These three sub-systems are fairly independent of one another.

By minimizing the responsibilities of widgets, we have arrived at the simplest widget type ever:

```python
Widget a  # Haskell
Widget<a> # C++
```

where the type `Widget` is parametrized by the (single) event type `a`. A text box would be `Widget String`, a button would be `Widget Unit`, and a color picker would be `Widget Color`.

How can we compose these widgets? In the simplest form, we need a function which takes two widgets, and returns their composition. For *composition in space*, this looks like a good start:

```python
# Haskell
join :: Widget a -> Widget b -> Widget (Either a b)

# C++
template <class a, class b>
Widget<std::variant<a, b>> join(Widget<a>, Widget<b>);
```

where `join` is the operator name, and `(Either a b)` is a tagged union (sum type) containing either `a`, or `b`. When `Widget a` is interacted with, we get `a`, When `Widget b` is interacted with, we get `b`. Our resulting widget is therefore even more shorter-lived than its constituents. But the definition above is no good: it quickly leads to complicated types. We can see that if we try to compose a 5-element list. We now have 5 different type parameters!

```python
# Haskell
let x = join a (join b (join c (join d e)))
     :: Widget (Either a (Either b (Either c (Either d e))))

# C++
Widget<std::variant<a, std::variant<b, std::variant<c, std::variant<d, e>>>> x =
    join(a, join(b, join(c, join(d, e))));
```

This is no good. We need to simplify our composition to prevent type proliferation. What about composing only widgets with the same event type?

```python
# Haskell
alt :: Widget a -> Widget a -> Widget a

# C++
template <class a>
Widget<a> alt(Widget<a>, Widget<a>);
```

Much better, the types remain simple forever. But is it even useful, didn't we simplify too much? It turns out it is, and we didn't. Our little `alt` function can do many things, including the previously-mentioned composition of widgets with different types.

Let's now examine **composition in time**. As stated above, widgets that come later depend on the results of earlier widgets. Our operator will take two widgets, where the second one is created from the result of the first one. It returns a composition of these two, which is yet another widget:

```haskell
bind :: Widget a -> (a -> Widget b) -> Widget b
#       ^ widget    ^-------------^    ^ result
#                  Widget generator
```

The resulting widget returns `b`, which is the return type of the second constituent widget. This enables further composition down the line. We don't even need to limit ourselves to a single event type for both widgets, as we did with `alt`. I hate to use the M-word, but this awfully looks like a monad: a more general concept of composition.

There is one last notable building block. We often need to transform the event type into a different one. From `Widget a`, we need to get a `Widget b` for some `a`, `b`. That is what the `map` is for:

```haskell
map :: (a -> b) -> Widget a -> Widget b
```

`map` simply takes a function `a -> b`, and uses it to transform the event fired by `Widget a` into `b`. The result is `Widget b`.

These are the fundamental building blocks we are left with:

* `Widget`: widget,
* `alt`: operator for composition in space,
* `bind`: operator for composition in time,
* `map`: operator for event transformation.

I think this looks rather elegant, almost forced by the nature of things. With a few simple orthogonal concepts, we can do everything there is to be done with widgets. (TODO: what about nesting?).

Now, the task is to assemble the puzzle back together, and to demonstrate that these are precisely the building blocks that we need for painless UI development.

## Putting it All Together

Can we build useful UIs from our four LEGO bricks? Let me take a shortcut, and demonstrate by example. There are now **four** UI libraries implementing these ideas in four different languages:

* [Concur](https://github.com/ajnsit/concur) - The original, written in Haskell.
* [Purescript Concur](https://github.com/purescript-concur/purescript-concur-react) - Well-maintained Purescript implementation for front-end programming.
* [Concur JS](https://github.com/ajnsit/concur-js) - The first port to an imperative language.
* [Python Concur](https://github.com/potocpav/python-concur) - Python port using ImGui instead of a virtual DOM.

The first three variants are written by [ajnsit](https://github.com/ajnsit). He's the one who came up with the idea. I created the Python implementation after seeing how delightful working in Purescript Concur was, and getting envious that I can't use it in scientific computing.

## Purescript example

This post would be underwhelming, if it didn't contain any usage examples. However, I don't know how to succintly present an example without diving into a concrete language's syntax. The concepts described above are clearly visible in Purescript code, which doesn't have to work around language limitations. Python and Javascript variants abuse the languages in fairly un-obvious way, but I will present an example in Python too. Feel free to skip Purescript example if it doesn't seem comprehensible.

A simple counter widget in Purescript:

```haskell
1  import Prelude
2  import Concur.Core (Widget)
3  import Concur.React (HTML)
4  import Concur.React.DOM as D
5  import Concur.React.Props as P
6
7  counterWidget :: ∀ a. Int -> Widget HTML a
8  counterWidget count = do
9      n <- D.div'
10          [ D.p' [D.text ("State: " <> show count)]
11         , D.button [P.onClick] [D.text "Increment"] $> count+1
12         , D.button [P.onClick] [D.text "Decrement"] $> count-1
13         ]
14     counterWidget n
15
16 main = runWidgetInDom "main" (counterWidget 0)
```

Let's start from the inside. This line creates a `button` widget, which reacts to the `onClick` event, and contains the text `"Increment"`. Quite self-explanatory:

```haskell
11         , D.button [P.onClick] [D.text "Increment"] $> count+1
```

This widget (basically) has the type `Widget X`, where `X` is an event type representing the `onClick` event. But we don't need to concern ourselves with `X`, because it is promptly thrown away and replaced by `Int` by the `$>` operator, which is a `map` in disguise. The result of the whole line is therefore a button widget with type `Widget Int`.

A second line we will look at is this one, creating a paragraph with the counter value:

```haskell
10         [ D.p' [D.text ("State: " <> show count)]
```

This paragraph doesn't create any events (it is passive), and just shows a given text. `<>` is a text concatenation operator. What is the type of a passive widget? Since the event is never observed (there is none), we can just go with the most flexible option, and say that it returns any type! It is, quite literally, `∀ a. Widget a`. This means we can compose passive widgets with any active widgets directly, which we use when we construct a `div` from the widget list:


```haskell
9    n <- D.div'
10         [ ...
13         ]    
```

Behind the scenes, `D.div'` uses the `alt` operator repeatedly to reduce the whole list into one `Widget Int`, which is immediately wrapped inside a `div` element. The `<-` operator waits for an event to be fired, and saves the event into `n` of type `Int`. We can work with `n` in subsequent lines:

```haskell
16   counterWidget n
```

This is the composition in time. The plumbing is implemented behind the scenes in terms of `bind`. This type of pattern is actually extremely common in practice, which is why Purescript has dedicated light-weight syntax sugar for this kind of composition ("do-notation"), and it's why we don't see `bind` explicitly. The line above just calls `counterWidget` recursively, with the new `n`. This is how we create a never-ending widget from our otherwise short-lived building blocks. Had this call not been here, the application would exit after a single interaction.

So the whole `counterWidget` exists forever: it doesn't fire any events. This is, similarly to the text-widget, reflected in the type:

```haskell
6  counterWidget :: ∀ a. Int -> Widget HTML a
--                                     ^^^^ ignore me
```

`counterWidget` also works with any event type `a`, it only needs to know which number to start with: that is the argument of type `Int`. Now that all the building blocks have been composed into a single `Widget`, our application is finished and it can be displayed on screen by calling:

```haskell
16 main = runWidgetInDom "main" (counterWidget 0)
```

OK, so it works in toy examples. But does it also work for real-world complex applications? The answer is simple: yes! And the proof is simple, too. Turns out that you can implement well-known and industry-proven architectures in a few lines of Concur. Concur subsumes The Elm Architecture, and React/Redux. It seems a bit like magic (or BS :o). But that's what you get when you choose good, minimal abstractions for the problem at hand.

React widgets are used directly. Here is Redux in Concur JS:

```js
function redux(state, render, update) {
  let action = yield* render(state)
  let newState = update(state, action)
  yield* redux(newState, render, update)
}
```

The Elm Architecture in Purescript Concur:
```haskell
tea :: forall a s m x. Monad m
    => s -> (s -> m a) -> (a -> s -> s) -> m x
tea s render update = go s where
    go st = render st >>= (flip update st >>> go)
```

The function above is more of a curiosity, because you can use Concur directly as Elm without any glue code whatsoever.

## Python Concur

As we saw in the Purescript example, many advanced language features were used to make it all work painlessly. Things like the do-notation are not present in mainstream languages. Can we make it work in Python? Turns out we can, by abusing the language a little. Python has a delightfully permissive type system, so the type shenanigans (event types must match) aren't really needed. What **is** a problem is painless composition in time using `bind`. We do not want to end up in a nested function mess like this:

```python
hello_world = bind(input("Name:"),
    lambda name: bind(input("Surname:"),
        lambda surname: text(f"Hello, {name} {surname}!")
        )
    )
```

We need to have a syntax sugar for composition in time, similarly to Purescript. Luckily, Python **synchronous** generators are monads (asynchronous are not 😢), and provide a rather nice notation:

```python
def hello_world():
    name = yield from input("Name:")
    yield

    surname = yield from input("Surname:")
    yield

    yield from text(f"Hello, {name} {surname}!")
```

The `yield` statements are a wart, caused by the inflexibility of Python generators. There are other issues I couldn't work around (two variants of `alt`, for example), but they are mostly cosmetic. Asynchronous generators couldn't be used, unfortunately, as they aren't a monad. Asynchronous code requires a bit of care, where in other Purescript variants, we get it for free.

Here is the counter application written in Python Concur:

```python
import concur as c

def counter_widget():
    counter = 0
    while True:
        action, _ = yield from c.orr([
            c.text(f"Count: {counter}"),
            c.button("Increment"),
            c.button("Decrement"),
            ])
        if action == "Increment":
            counter += 1
        elif action == "Decrement":
            counter -= 1
        yield


if __name__ == "__main__":
    c.main("Counter", counter_widget(), 500, 500)
```

It is hopefully obvious by now, how the basic concepts we defined earlier enable the implementation of Python Concur. Composition in time is achieved by the loop and the `yield from` generator syntax. Composition in space is achieved by the `c.orr` function, which is just a repeated application of `alt` over the list of widgets.

As using tagged unions and `map` in Python is syntactically heavy, I opted to use widgets which automatically tag their values with the name of the widget. Therefore, a `c.button("Increment")` returns a tuple `("Increment", None)`, which is pattern-matched by the `if-elif` block below.

## Why hasn't it been done before?

If it's such a good idea, why this hadn't been done before?

* It actually has been nearly done before. Just not bottom-up as we did here. The Elm Architecture and React+Redux seem to be subsets of Concur, and their programming style is similar.
* Object-oriented mindset insists on complecting state & behavior. This prevents simplification.
* Mainstream programming languages lack sum types, which are crucial for events. Or a dynamic type system, but that is non-obvious.
* Virtual DOM or ImGui are needed for implementation. They haven't become mainstream until recently.

## Conclusion

Composition in time hasn't been identified as a concept, or tackled head-on by traditional UI libraries. They tend to dedicate much effort and language syntax to composition in space, while they neglect composition in time and handle it implicitly by state mutation. We, on the other hand, use language constructs for composition in time, not composition in space. It is a much better fit: the dependency on previous values in time composition is nicely enforced by the top-down control flow of programming languages. Composition in space doesn't have an inherent order, so lists are a much better fit.

 We identified the simplest atomic construct we could, which are still sufficient for UI creation. By doing it, we arrived at a surprisingly simple, yet powerful abstraction around widget composition. This abstraction allows us to be simultaneously simpler and more powerful than well-known libraries, such as React/Redux and Elm. And **way** simpler than MVC, OOP, event-driven UI libraries.





# %%
