
# This files demonstrates the IO templates syntax.
# Text following a "#" are comments

# This is the first example
# The syntax for input prompts is: "prompt message": "input"
# The outputs are preceeded by an "-->" arrow.
"self: ": "a"
"y: ": "b"
--> "result: ab"

# Different examples are separated by two newlines
# The quotes in the interaction strings are largely unecessary, unless
# one needs a very precise control of whitespace
"self: ": b
"y: ": c
--> "result: bc"

# Since the colon character ":" may appear so frequently in input
# prompts, we also accept the double colon "::" syntax
self:: foo
y:: bar
--> "result: foobar"

# Finally, interaction can be specified in a single line for compactness
self:: 1; y:: 2 --> "result: 3"

# Remember to separate each test by at least two newlines!
self:: 1.0; y:: 2.0 --> "result: 3.0"

self:: 1; y:: 5 --> "result: 6"

self:: 1; y:: 5.0 --> "result: 6.0"

self:: 2.0; y:: 5.0 --> "result: 7.0" # we can put comments here too!
