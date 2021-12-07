# Qt User Interface Compiler version 6.2.2

```cmd
Usage: pyside6-uic.exe [options] [uifile]
```

## Options
* -?, -h, --help                  Displays help on commandline options.
* --help-all                      Displays help including Qt specific options.
* -v, --version                   Displays version information.
* -d, --dependencies              Display the dependencies.
* -o, --output <file>             Place the output into <file>
* -a, --no-autoconnection         Do not generate a call to
                                  QObject::connectSlotsByName().
* -p, --no-protection             Disable header protection.
* -n, --no-implicit-includes      Disable generation of #include-directives.
* --postfix <postfix>             Postfix to add to all generated classnames.
* --tr, --translate <function>    Use <function> for i18n.
* --include <include-file>        Add #include <include-file> to <file>.
* -g, --generator <python|cpp>    Select generator.
* -c, --connections <pmf|string>  Connection syntax.
* --idbased                       Use id based function for i18n
* --from-imports                  Python: generate imports relative to '.'
* --star-imports                  Python: Use * imports

## Arguments
* [uifile]                        Input file (*.ui), otherwise stdin.
