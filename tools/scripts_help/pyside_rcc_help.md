# Qt Resource Compiler version 6.2.2

Usage:
```cmd
pyside6-rcc.exe [options] inputs
```


## Options

* -?, -h, --help

    `Displays help on commandline options.`


* --help-all
    `Displays help including Qt specific options.`
* -v, --version                         Displays version information.
* -o, --output <file>                   Write output to <file> rather than
                                        stdout.
* -t, --temp <file>                     Use temporary <file> for big resources.
* --name <name>                         Create an external initialization
                                        function with <name>.
* --root <path>                         Prefix resource access path with root
                                        path.
* --compress-algo <algo>                Compress input files using algorithm
                                        <algo> ([zlib], none).
* --compress <level>                    Compress input files by <level>.
* --no-compress                         Disable all compression. Same as
                                        --compress-algo=none.
* --no-zstd                             Disable usage of zstd compression.
* --threshold <level>                   Threshold to consider compressing
                                        files.
* --binary                              Output a binary file for use as a
                                        dynamic resource.
* -g, --generator <cpp|python|python2>  Select generator.
* --pass <number>                       Pass number for big resources
* --namespace                           Turn off namespace macros.
* --verbose                             Enable verbose mode.
* --list                                Only list .qrc file entries, do not
                                        generate code.
* --list-mapping                        Only output a mapping of resource paths
                                        to file system paths defined in the .qrc
                                        file, do not generate code.
* -d, --depfile <file>                  Write a depfile with the .qrc
                                        dependencies to <file>.
* --project                             Output a resource file containing all
                                        files from the current directory.
* --format-version <number>             The RCC format version to write

## Arguments
* inputs                                Input files (*.qrc).
