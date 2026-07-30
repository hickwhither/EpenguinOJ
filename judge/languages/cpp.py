class CPPExecutor:
    language_id = "cpp"
    file_extension = "cpp"
    compiled_file_extension = "out"
    version = "g++ --version"
    command = "/usr/bin/g++ -std=c++14 -Wall -DONLINE_JUDGE -O2 -lm -fmax-errors=5 -march=native -s -Wl,-z,stack-size=66060288 {source} -o {prog}"
    executable = ""
    example="""#include<iostream>
    int main(){
        std::cout << "Hello, world!";
        return 0;
    }"""