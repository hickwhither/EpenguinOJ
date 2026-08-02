BASE_CXXFLAGS = [
    "-std=c++14",
    "-Wall",
    "-lm",
    "-fmax-errors=5",
    "-march=native",
    "-s",
    "-Wl,-z,stack-size=66060288",
    "-I",
    ".",
]

CXXFLAGS_O2 = BASE_CXXFLAGS + ["-O2"]
CXXFLAGS_O0 = BASE_CXXFLAGS + ["-O0"]
