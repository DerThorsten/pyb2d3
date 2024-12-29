from pyb2d.py_core.vec2 import *
from pyb2d import MyVec2,length
from math import sqrt

def mylength(a):
    return sqrt(a[0]**2 + a[1]**2)

def pure_tuple_math(n=1000):
    for i in range(n):
        a = (i,i+1)
        # b = (i-1,i)
        # c = (a[0] * b[0], a[1] * b[1])

        # #  compute absolut norm
        norm = sqrt(a[0]**2 + a[1]**2)


def spure_tuple_math(n=1000):
    for i in range(n):
        a = (i,i+1)
        # b = (i-1,i)
        # c = (a[0] * b[0], a[1] * b[1])

        # #  compute absolut norm
        norm = mylength(a)



def cpp_tuple_math(n=1000):
    #  use MyVec2
    for i in range(n):
        a = MyVec2(i,i+1)
        # b = MyVec2(i-1,i)
        # c = a * b
        norm = length(a)

def test_tuple_math(benchmark):
    benchmark(pure_tuple_math)


def test_cpp_tuple_math(benchmark):
    benchmark(cpp_tuple_math)


def test_spure_tuple_math(benchmark):
    benchmark(spure_tuple_math)