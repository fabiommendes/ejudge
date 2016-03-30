template = '''
# This files demonstrates the IO templates syntax.
# Text following a "#" are comments

# This is the first example
# The syntax for input prompts is: "prompt message": "input"
# The outputs are preceeded by an "-->" arrow.
"x: ": "a"
"y: ": "b"
--> "result: ab"

# Different examples are separated by two newlines
# The quotes in the interaction strings are largely unecessary, unless
# one needs a very precise control of whitespace
"x: ": b
"y: ": c
--> "result: bc"

# Since the colon character ":" may appear so frequently in input
# prompts, we also accept the double collon "::" syntax
x:: foo
y:: bar
--> "result: foobar"

# Finally, interaction can be specified in a single line for compactness
x:: 1; y:: 2 --> "result: 3"

# Remember to separate each test by at least two newlines!
x:: 1.0; y:: 2.0 --> "result: 3.0"

x:: 1; y:: 5 --> "result: 6"

x:: 1; y:: 5.0 --> "result: 6.0"

x:: 2.0; y:: 5.0 --> "result: 7.0" # we can put comments here too!
'''

if __name__ == '__main__':
    with open('simple.io', 'w') as F:
        F.write(template)
