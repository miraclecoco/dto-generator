import os
import sys
from os import path
from glob import glob
from colorama import Fore

from internal import spec
from internal.codegen.php import PHPGenerator
from internal.codegen.ts import TSGenerator


def main():
    lang = sys.argv[1] if len(sys.argv) >= 2 else ''
    spec_dir = sys.argv[2] if len(sys.argv) >= 3 else ''

    if not lang:
        print(
            Fore.RED + "[FAIL] 'lang' must be specified".format(spec_dir) + Fore.RESET)
        return

    if not path.isdir(spec_dir):
        print(
            Fore.RED + "[FAIL] could not find directory '{0}'".format(spec_dir) + Fore.RESET)
        return

    if lang == 'php':
        gen = PHPGenerator()
    elif lang == "ts":
        gen = TSGenerator()
    else:
        print(
            Fore.RED + "[FAIL] unsupported lang '{0}'".format(lang) + Fore.RESET)
        return

    spec_dir = path.abspath(spec_dir)

    spec_pattern = path.join(spec_dir, "**", "*.json")
    print(Fore.GREEN +
          "[DEBUG] using pattern '{0}' for search".format(spec_pattern) + Fore.RESET)

    spec_files = glob(spec_pattern, recursive=True)

    print(Fore.CYAN +
          "[INFO] {0} spec(s) was found".format(len(spec_files)) + Fore.RESET)
    for spec_file in spec_files:
        print(Fore.CYAN + "       {0}".format(spec_file) + Fore.RESET)

    for spec_file in spec_files:
        sp = spec.parse_file(spec_file)

        if not path.isdir(sp.out_dir()):
            os.makedirs(sp.out_dir())
            print(
                Fore.YELLOW + "[WARN] output directory '{0}' has been created".format(sp.out_dir()) + Fore.RESET)

        out_dir = path.abspath(sp.out_dir())
        out_file = path.join(out_dir, "{0}{1}".format(gen.get_clazz(sp), gen.get_extension()))

        with open(out_file, "w", encoding="utf-8") as fp:
            gen.generate(sp, fp)


if __name__ == '__main__':
    main()
