import json
import signal
import sys
from functools import partial
from multiprocessing import Pool
from typing import List

from black import TargetVersion, WriteBack

from jupyterblack.arguments import parse_args
from jupyterblack.parser import BlackFileModeKwargs, check_jupyter_file, format_jupyter_file
from jupyterblack.util.files import check_ipynb_extensions, check_paths_exist
from jupyterblack.util.targets import targets_to_files


def main() -> None:
    """Read jupyterblack CLI arguments."""
    run(sys.argv[1:])


def init_worker() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run(args: List[str]) -> None:
    # pylint: disable=too-many-locals,too-many-branches
    namespace = parse_args(*args)

    targets: List[str] = namespace.targets
    skip_string_normalization: bool = namespace.skip_string_normalization
    is_check: bool = namespace.check
    is_diff: bool = False  # namespace.diff
    line_length: int = namespace.line_length
    is_pyi: bool = namespace.pyi
    n_workers: int = namespace.workers
    show_invalid_code: bool = namespace.show_invalid_code

    if namespace.target_version is not None:
        target_versions = {TargetVersion[val.upper()] for val in namespace.target_version}
    else:
        target_versions = set()

    check_paths_exist(targets)

    write_back = WriteBack.from_configuration(check=is_check, diff=is_diff)
    black_file_mode_kwargs = BlackFileModeKwargs(
        line_length=line_length, string_normalization=not skip_string_normalization
    )
    if is_pyi:  # Not sure if older versions of black have "is_pyi"
        black_file_mode_kwargs = BlackFileModeKwargs(  # type: ignore[misc]
            **black_file_mode_kwargs, is_pyi=is_pyi,
        )
    if target_versions:
        black_file_mode_kwargs = BlackFileModeKwargs(  # type: ignore[misc]
            **black_file_mode_kwargs, target_versions=target_versions
        )

    # Transform supplied targets (directories or files) to files
    target_files = targets_to_files(targets)
    check_ipynb_extensions(target_files)

    if write_back is WriteBack.YES:
        if n_workers == 1:  # No need to set up a process Pool for a single worker (slow when run on a single file)
            format_results = [format_jupyter_file(file, black_file_mode_kwargs) for file in target_files]
        else:
            with Pool(processes=n_workers, initializer=init_worker) as process_pool:
                format_results = process_pool.map(
                    partial(format_jupyter_file, kwargs=black_file_mode_kwargs), target_files
                )
        if show_invalid_code:
            print("WARN: Detected the following invalid code snippets:")
            print(json.dumps({format_res.file: format_res.invalid_report for format_res in format_results}, indent=4))
        print("All done!")
    elif write_back is WriteBack.CHECK:

        if n_workers == 1:  # No need to set up a process Pool for a single worker
            check_results = [check_jupyter_file(file, black_file_mode_kwargs) for file in target_files]
        else:
            with Pool(processes=n_workers, initializer=init_worker) as process_pool:
                check_results = process_pool.map(
                    partial(check_jupyter_file, kwargs=black_file_mode_kwargs), target_files,
                )

        files_not_formatted = [res.file for res in check_results if not res.is_okay]
        if show_invalid_code:
            print("WARN: Detected the following invalid code snippets:")
            print(json.dumps({res.file: res.invalid_report for res in check_results}, indent=4))
        if not files_not_formatted:
            print("All good! Supplied targets are already formatted with black.")
        else:
            raise SystemExit("Files that need formatting:\n  - " + "\n  - ".join(files_not_formatted))
    else:
        raise SystemExit(f"WriteBack option: {write_back} not yet supported")


if __name__ == "__main__":
    main()
