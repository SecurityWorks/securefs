#!/usr/bin/env python3
import subprocess
import os
import tempfile
import argparse
import shutil


def check_call(*args):
    print("Executing", args)
    subprocess.check_call(args)


def get_build_root(build_root: str) -> str:
    if build_root:
        os.makedirs(build_root, exist_ok=True)
        return build_root
    base_tmp_dir = None
    if os.path.isdir("/dev/shm"):
        base_tmp_dir = "/dev/shm"
    return tempfile.mkdtemp(prefix="securefs", dir=base_tmp_dir)


def _unchecked_get_vcpkg_cmake_file(vcpkg_root: str | None) -> str:
    subpath = "scripts/buildsystems/vcpkg.cmake"
    vcpkg_root = vcpkg_root or os.environ.get("VCPKG_ROOT")
    if vcpkg_root:
        return os.path.join(vcpkg_root, subpath)
    exe_path = shutil.which("vcpkg")
    if exe_path:
        vcpkg_root = os.path.dirname(exe_path)
        return os.path.join(vcpkg_root, subpath)
    vcpkg_root = os.path.expanduser("~/vcpkg")
    return os.path.join(vcpkg_root, subpath)


def get_vcpkg_cmake_file(vcpkg_root: str | None) -> str:
    result = _unchecked_get_vcpkg_cmake_file(vcpkg_root)
    if not os.path.isfile(result):
        raise ValueError(
            "Cannot find vcpkg installation by heuristic. Please specify --vcpkg_root explicitly."
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vcpkg_root",
        help="The root of vcpkg repository",
        default=None,
    )
    parser.add_argument(
        "--build_root",
        help="The root of build directory. If unset, a temporary directory will be used.",
        default="",
    )
    parser.add_argument(
        "--enable_test", default=False, help="Enable all tests", action="store_true"
    )
    parser.add_argument(
        "--enable_unit_test",
        default=False,
        help="Run unit test after building to ensure correctness",
        action="store_true",
    )
    parser.add_argument(
        "--enable_integration_test",
        default=False,
        help="Run integration test after building to ensure correctness",
        action="store_true",
    )
    parser.add_argument(
        "--triplet",
        default="" if os.name != "nt" else "x64-windows-static-md",
        help="Override the default vcpkg triplet",
    )
    parser.add_argument(
        "--cmake_defines",
        default=[],
        nargs="*",
        help="Additional CMake definitions. Example: FOO=BAR",
    )
    args = parser.parse_args()

    if args.enable_test:  # For backwards compat
        args.enable_unit_test = True
        args.enable_integration_test = True

    source_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(get_build_root(args.build_root))
    configure_args = [
        "cmake",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_TOOLCHAIN_FILE={get_vcpkg_cmake_file(args.vcpkg_root)}",
    ]
    if args.triplet:
        configure_args.append("-DVCPKG_TARGET_TRIPLET=" + args.triplet)
    if not args.enable_unit_test:
        configure_args.append("-DSECUREFS_ENABLE_UNIT_TEST=OFF")
    if not args.enable_integration_test:
        configure_args.append("-DSECUREFS_ENABLE_INTEGRATION_TEST=OFF")
    for pair in args.cmake_defines:
        configure_args.append("-D" + pair)
    configure_args.append(source_dir)

    check_call(*configure_args)
    check_call("cmake", "--build", ".", "--config", "Release")
    if args.enable_unit_test or args.enable_integration_test:
        check_call("ctest", "-V", "-C", "Release")
    print(
        "Build succeeds. Please copy the binary somewhere in your PATH:",
        os.path.realpath("./securefs"),
    )


if __name__ == "__main__":
    main()
