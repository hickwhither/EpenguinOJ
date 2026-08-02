from cxx import CXXFLAGS_O2

class CPPExecutor:
    language_id = "cpp"
    file_extension = "cpp"
    compiled_file_extension = "out"
    version = "g++ --version"
    command = "/usr/bin/g++ " + " ".join(CXXFLAGS_O2 + ["-DONLINE_JUDGE"]) + " {source} -o {prog}"
    executable = ""
    example="""#include<iostream>
    int main(){
        std::cout << "Hello, world!";
        return 0;
    }"""
