def foo(x: int, y: int, z: int):
    print (x,y,z)


d = {'x': 1, 'y': 2}

foo(**d, z=4)