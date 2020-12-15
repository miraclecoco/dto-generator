import os
import sys
from os import path
from glob import glob
from colorama import Fore

from internal import spec
from internal.gen.php import PHPGenerator


def main():
    spec_dir = sys.argv[1] if len(sys.argv) > 1 else ''
    if not path.isdir(spec_dir):
        print(
            Fore.RED + "[FAIL] could not find directory '{0}'".format(spec_dir) + Fore.RESET)
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
        gen = PHPGenerator()
        s = gen.generate(sp)

        if not path.isdir(sp.out_dir()):
            os.makedirs(sp.out_dir())
            print(
                Fore.YELLOW + "[WARN] output directory '{0}' has been created".format(sp.out_dir()) + Fore.RESET)

        out_dir = path.abspath(sp.out_dir())

        with open(path.join(out_dir, "{0}.php".format(sp.source().clazz())), "w", encoding="utf-8") as fp:
            fp.write(s)


if __name__ == '__main__':
    main()
