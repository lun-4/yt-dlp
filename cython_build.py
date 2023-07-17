from pathlib import Path
import shlex
from subprocess import check_output


def main():
    modfolder = Path.cwd() / "yt_dlp"
    (Path.cwd() / "cython_out").mkdir(exist_ok=True)
    print("compiling python to c")
    for source_file in modfolder.glob("**/*.py"):
        if "__pyinstaller" in str(source_file):
            print("skip, pyinstaller")
            continue
        if "postprocessor/ffmpeg.py" in str(source_file):
            print("skip, postprocessor/ffmpeg.py")
            continue

        relative_path = source_file.relative_to(modfolder)
        components = str(relative_path).split("/")
        components[-1] = components[-1].replace(".py", "")
        target_file = source_file.with_name(source_file.name.replace(".py", ".c"))
        module_name = "yt_dlp" + "." + ".".join(components)
        print(source_file, target_file, module_name)

        if not target_file.exists():
            args = ["env/bin/cythonize"]
            args.extend(
                [
                    # "-o",
                    # str(target_file),
                    # "--module-name",
                    # module_name,
                    "-3",
                    str(source_file),
                ]
            )

            print(shlex.join(args))
            check_output(args)

        # cython will emit PyInit_common() or PyInit__deprecated() or something else
        # depending on the name of the file, which is not good, because we want to compile
        # everything under a single binary.

        # the hack here is to just replace those functions with more "unique" variants
        # using string replace

        if (
            "common.c" in str(target_file)
            or "_deprecated.c" in str(target_file)
            or "_legacy.c" in str(target_file)
        ):
            print("i hate this one")
            with target_file.open(mode="r") as fd:
                target_contents = fd.read()

            target_contents = (
                target_contents.replace(
                    "PyInit_common", f"PyInit_{components[-2]}_{components[-1]}"
                )
                .replace(
                    "PyInit__deprecated", f"PyInit_{components[-2]}_{components[-1]}"
                )
                .replace("PyInit__legacy", f"PyInit_{components[-2]}_{components[-1]}")
            )
            with target_file.open(mode="w") as fd:
                fd.write(target_contents)

    args = ["env/bin/cython", "--embed=main", "-3", "yt_dlp/lunar_entry.py"]
    print(shlex.join(args))
    check_output(args)

    ytdlp = Path.cwd() / "yt_dlp"
    print("compiling c object files")
    compile_sources = list(Path.cwd().glob("yt_dlp/**/*.c"))
    for source in compile_sources:
        object_file = source.with_name(source.name.replace(".c", ".o"))
        print(source, object_file)
        if not object_file.exists():
            # TODO use CC variable
            args = [
                "gcc",
                "-I/usr/include/python3.11",
                "-c",
                str(source),
            ]

            print(shlex.join(args))
            check_output(
                args,
                cwd=source.parent,
            )

    objects = [str(p) for p in ytdlp.glob("**/*.o")]

    print("final link")
    args = [
        "gcc",
        "-lpython3.11",
        "-I/usr/include/python3.11",
        *objects,
        "-o",
        "epic_ytdlp",
    ]

    print(shlex.join(args))
    check_output(args)


if __name__ == "__main__":
    main()
