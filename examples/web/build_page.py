"""Build a static page running the pyb2d3 sandbox (WebGL frontend) in the browser.

The page uses the pyjs npm package; pyb2d3, PyOpenGL and numpy are installed
at runtime from conda channels (local channels are copied into the
page and listed first), the sandbox sources (examples/) are packed into one
archive the page mounts at /examples.

    python examples/web/build_page.py --out build/web_sandbox \\
        --pyjs <pyjs npm package dir (with dist/ + assets/)> \\
        --channel emscripten_forge/output --channel <recipes>/output
    python -m http.server -d build/web_sandbox 8000   # open http://localhost:8000

Without --pyjs the page loads the pyjs npm package from jsDelivr (--pyjs-url).
"""

import argparse
import json
import shutil
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
# the python packages of examples/ the sandbox needs
# (pyb2d3_sandbox_opengl: only its GL renderers + shaders are used, no imgui)
SANDBOX_PACKAGES = ["pyb2d3_sandbox", "pyb2d3_sandbox_opengl", "pyb2d3_sandbox_webgl", "pyb2d3_samples"]
# conda packages installed at runtime
# (pillow: text rendering of some samples, examples_common/text.py)
CONDA_PACKAGES = ["pyb2d3", "pyopengl", "numpy", "pillow"]
DEFAULT_CHANNELS = ["https://repo.prefix.dev/emscripten-forge/6x", "conda-forge"]
# python of the pyjs runtime (site-packages path of mounted packages)
PYTHON_VERSION = "3.14"
DEFAULT_PYJS_URL = "https://cdn.jsdelivr.net/npm/@derthorsten/pyjs/dist/index.js"
# the subdirs of a channel the page can use
CHANNEL_SUBDIRS = ["noarch", "emscripten-wasm32", "emscripten-wasm64"]


def _skip_cache(tarinfo):
    """tar filter: no bytecode caches"""
    if "__pycache__" in tarinfo.name or tarinfo.name.endswith(".pyc"):
        return None
    return tarinfo


def pack_examples(out):
    """examples.tar.gz with the sandbox packages (mounted at /examples)"""
    with tarfile.open(out / "examples.tar.gz", "w:gz") as tar:
        for name in SANDBOX_PACKAGES:
            tar.add(EXAMPLES / name, arcname=name, filter=_skip_cache)


def conda_pkg_name(conda_pkg):
    """package name of a conda package file (name-version-build.tar.bz2)"""
    return conda_pkg.name.rsplit("-", 2)[0]


def pack_local_pkg(out, conda_pkg):
    """<name>.tar.gz with the site-packages content of a built conda package
    (.tar.bz2), unpacked into site-packages by the page (untarjs): a local
    build used without solving it from a channel (where a published package
    of the same name could win). Returns the archive name."""
    prefix = f"lib/python{PYTHON_VERSION}/site-packages/"
    archive = f"{conda_pkg_name(conda_pkg)}.tar.gz"
    with tarfile.open(conda_pkg, "r:bz2") as src, tarfile.open(out / archive, "w:gz") as dst:
        members = [m for m in src.getmembers() if m.isfile() and m.name.startswith(prefix)]
        if not members:
            raise SystemExit(f"{conda_pkg} has no files in {prefix}")
        for member in members:
            data = src.extractfile(member)
            member.name = member.name[len(prefix):]
            dst.addfile(member, data)
    return archive


def copy_channel(src, dst):
    """copy the usable subdirs of a local channel (repodata.json + packages)"""
    for subdir in CHANNEL_SUBDIRS:
        if (src / subdir / "repodata.json").exists():
            shutil.copytree(src / subdir, dst / subdir, ignore=shutil.ignore_patterns(".*"))
    if not dst.exists():
        raise SystemExit(f"{src} is not a conda channel (no <subdir>/repodata.json)")


def build(out, pyjs_dir, pyjs_url, channels, packages, local_pkgs=()):
    """create the page dir `out`"""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in ["index.html", "main.js"]:
        shutil.copy(HERE / name, out / name)
    pack_examples(out)
    # archives the page unpacks (untarjs) before python starts
    archives = [{"url": "examples.tar.gz", "path": "/examples"}]
    for conda_pkg in local_pkgs:
        archive = pack_local_pkg(out, conda_pkg)
        archives.append({"url": archive, "path": f"/lib/python{PYTHON_VERSION}/site-packages"})
        packages = [p for p in packages if p != conda_pkg_name(conda_pkg)]

    if pyjs_dir is not None:
        shutil.copytree(pyjs_dir, out / "pyjs", ignore=shutil.ignore_patterns("node_modules"))
        pyjs_entry = "./pyjs/dist/index.js"
    else:
        pyjs_entry = pyjs_url

    channel_urls = []
    for i, src in enumerate(channels):
        copy_channel(src, out / "channels" / str(i))
        channel_urls.append(f"channels/{i}")  # relative: resolved against the page

    config = {
        "pyjs": pyjs_entry,
        "local_channels": channel_urls,
        "channels": DEFAULT_CHANNELS,
        "packages": packages,
        "archives": archives,
    }
    (out / "config.json").write_text(json.dumps(config, indent=2))


def main():
    """command line"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, help="page directory (recreated)")
    parser.add_argument("--pyjs", type=Path, help="local pyjs npm package dir (dist/ + assets/)")
    parser.add_argument("--pyjs-url", default=DEFAULT_PYJS_URL, help="pyjs entry module without --pyjs")
    parser.add_argument(
        "--channel", type=Path, action="append", default=[],
        help="local conda channel (e.g. a rattler-build output dir), copied into the page; repeatable",
    )
    parser.add_argument(
        "--package", action="append", default=None,
        help=f"conda package to install (default: {' '.join(CONDA_PACKAGES)}); repeatable",
    )
    parser.add_argument(
        "--local-pkg", type=Path, action="append", default=[],
        help="a locally built conda package (.tar.bz2, e.g. pyb2d3, pyopengl): its "
        "site-packages content is packed + unpacked by the page instead of "
        "installing the package from a channel; repeatable",
    )
    args = parser.parse_args()
    build(
        args.out.resolve(), args.pyjs, args.pyjs_url, args.channel,
        args.package or CONDA_PACKAGES, args.local_pkg,
    )
    print(f"page written to {args.out}, serve it e.g. with: python -m http.server -d {args.out} 8000")


if __name__ == "__main__":
    main()
