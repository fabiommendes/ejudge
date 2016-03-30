def conv(x):
    try:
        x = float(x) if '.' in x else int(x)
    except ValueError:
        pass
    return x

x = conv(input('x: '))
y = conv(input('y: '))
print('result: ', x + y)
