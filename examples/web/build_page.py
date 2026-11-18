"""Build a static page running the pyb2d3 sandbox (WebGL frontend) in the browser.

The page brings everything it needs to start: pyjs (python; the pinned npm package,
or a local pyjs dir with --pyjs) and two content-hashed archives that pyjs unpacks
before python starts (and caches; it also preloads their shared libraries): the
sandbox sources (examples/, mounted at /examples) and the packages: the local pyb2d3
build (`pixi run emscripten`) with numpy (+ openblas) and PyOpenGL, downloaded from
emscripten-forge at build time, without tests, headers, docs, ...: no package install
(mamba) in the browser, no CDN needed to start.

    pixi run emscripten
    python examples/web/build_page.py --out build/web_sandbox
    python -m http.server -d build/web_sandbox 8000   # open http://localhost:8000
    pixi run -e web-test web-test                     # the page in headless chromium

The page is plain ES modules (index.html, main.js, editor.js), copied as they are:
no package.json, no bundler. Only the code editor (Monaco) comes from a CDN (cdnjs),
the logic lives in python (pyb2d3_sandbox_webgl). A package.json + bundler would only
pay off with TypeScript, npm dependencies that are not on a CDN, or unit tests of the JS.
"""

import argparse
import contextlib
import gzip
import hashlib
import json
import re
import shutil
import tarfile
import tomllib
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
REPO = EXAMPLES.parent
# the python packages of examples/ the sandbox needs
# (pyb2d3_sandbox_opengl: only its GL renderers + shaders are used, no imgui)
SANDBOX_PACKAGES = [
    "pyb2d3_sandbox",
    "pyb2d3_sandbox_opengl",
    "pyb2d3_sandbox_webgl",
    "pyb2d3_samples",
]
# packed with the local pyb2d3 build, downloaded from emscripten-forge into
# PACKAGE_CACHE
CHANNEL = "https://repo.prefix.dev/emscripten-forge/6x/emscripten-wasm32"
PACKAGES = ["numpy", "openblas", "pyopengl"]
PACKAGE_CACHE = REPO / "build" / "conda-packages"
# not needed to run anything: tests, headers, docs, metadata, Windows DLLs, ...
DROP_DIRS = {"tests", "testing", "f2py", "distutils", "include", "__pycache__", "DLLS", "doc"}
DROP_SUFFIXES = (".pyi", ".pxd", ".h", ".a", ".pc", ".cmake", ".pyc", ".c", ".cpp")
# pyjs, pinned (a new one may bring another python), copied into the page from its
# npm package. Update both together: the packed packages are built for PYTHON_VERSION
# (the npm package.json says which python a pyjs has: "pyjs": {"python": ...})
PYJS_VERSION = "5.2.0"
PYTHON_VERSION = "3.14"
PYJS_TARBALL = f"https://registry.npmjs.org/@derthorsten/pyjs/-/pyjs-{PYJS_VERSION}.tgz"


def local_pyb2d3_build():
    """the newest emscripten build of this version of pyb2d3 (`pixi run emscripten`)"""
    version = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
    output = REPO / "emscripten_forge" / "output" / "emscripten-wasm32"
    builds = sorted(output.glob(f"pyb2d3-{version}-*.tar.bz2"), key=lambda p: p.stat().st_mtime)
    if not builds:
        raise SystemExit(
            f"no emscripten build of pyb2d3 {version} in {output}: pixi run emscripten"
        )
    return builds[-1]


@contextlib.contextmanager
def tar_gz(path):
    """a .tar.gz writer whose bytes depend on the content only (no time stamps, owners):
    an unchanged archive keeps its content hash, and the browsers their cached copy"""
    with gzip.GzipFile(path, "wb", mtime=0) as gz, tarfile.open(fileobj=gz, mode="w") as tar:
        yield tar


def _normalized(tarinfo):
    """tar filter: no time stamps / owners (see tar_gz), no bytecode caches"""
    if "__pycache__" in tarinfo.name or tarinfo.name.endswith(".pyc"):
        return None
    tarinfo.mtime, tarinfo.uid, tarinfo.gid, tarinfo.uname, tarinfo.gname = 0, 0, 0, "", ""
    return tarinfo


def pack_examples(out):
    """examples.tar.gz with the sandbox packages (mounted at /examples)"""
    with tar_gz(out / "examples.tar.gz") as tar:
        for name in SANDBOX_PACKAGES:
            tar.add(EXAMPLES / name, arcname=name, filter=_normalized)


def _version_key(info):
    """sort key: newest version, then build number, then upload time"""
    version = tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-_]", info["version"]))
    return version, info.get("build_number", 0), info.get("timestamp", 0)


def _download(url):
    """the bytes at `url` (the channel's storage refuses urllib's default user agent)"""
    request = urllib.request.Request(url, headers={"User-Agent": "pyb2d3-build-page"})
    with urllib.request.urlopen(request) as response:
        return response.read()


def fetch_packages(names, cache=PACKAGE_CACHE):
    """the newest emscripten-wasm32 builds of `names` (for PYTHON_VERSION) from
    emscripten-forge, downloaded into `cache` once. Returns their paths."""
    packages = json.loads(_download(f"{CHANNEL}/repodata.json"))["packages"]
    python_build = f"py{PYTHON_VERSION.replace('.', '')}"
    cache.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        builds = {f: i for f, i in packages.items() if i["name"] == name}
        # python packages: builds for this python only
        if any(i["build"].startswith("py") for i in builds.values()):
            builds = {f: i for f, i in builds.items() if i["build"].startswith(python_build)}
        if not builds:
            raise SystemExit(f"no {name} for python {PYTHON_VERSION} in {CHANNEL}")
        filename = max(builds, key=lambda f: _version_key(builds[f]))
        path = cache / filename
        if not path.exists():
            print(f"downloading {filename}")
            path.write_bytes(_download(f"{CHANNEL}/{filename}"))
        paths.append(path)
    return paths


def _keep(name):
    """files of a conda package needed at runtime (not tests, headers, metadata, ...)"""
    parts = name.split("/")
    return not (
        parts[0] in ("info", "etc", "share", "bin")
        or any(p in DROP_DIRS or p.endswith(".dist-info") for p in parts)
        or name.endswith(DROP_SUFFIXES)
    )


def pack_packages(out, conda_pkgs):
    """packages.tar.gz: the runtime files of the conda packages (.tar.bz2), paths
    relative to the environment prefix (unpacked at /; pyjs preloads its shared
    libraries)"""
    size = 0
    with tar_gz(out / "packages.tar.gz") as dst:
        for conda_pkg in conda_pkgs:
            with tarfile.open(conda_pkg, "r:bz2") as src:
                for member in src.getmembers():
                    if member.isfile() and _keep(member.name):
                        dst.addfile(_normalized(member), src.extractfile(member))
                        size += member.size
    print(f"packed {', '.join(p.name for p in conda_pkgs)}: {size / 1e6:.1f} MB unpacked")


def copy_pyjs(out, pyjs_dir=None):
    """pyjs into the page: a local pyjs npm package dir (dist/ + assets/), else the
    pinned npm package (downloaded once): its dist/ and wasm32 assets. Returns the
    entry module's url (the version in the dir name: no stale browser cache)"""
    if pyjs_dir is not None:
        shutil.copytree(pyjs_dir, out / "pyjs-dev", ignore=shutil.ignore_patterns("node_modules"))
        return "./pyjs-dev/dist/index.js"
    tarball = PACKAGE_CACHE / f"pyjs-{PYJS_VERSION}.tgz"
    if not tarball.exists():
        print(f"downloading {PYJS_TARBALL}")
        PACKAGE_CACHE.mkdir(parents=True, exist_ok=True)
        tarball.write_bytes(_download(PYJS_TARBALL))
    target = out / f"pyjs-{PYJS_VERSION}"
    with tarfile.open(tarball, "r:gz") as tar:
        for member in tar.getmembers():
            name = member.name.removeprefix("package/")
            if member.isfile() and name.startswith(("dist/", "assets/")) and "wasm64" not in name:
                (target / name).parent.mkdir(parents=True, exist_ok=True)
                (target / name).write_bytes(tar.extractfile(member).read())
    return f"./pyjs-{PYJS_VERSION}/dist/index.js"


def build(out, pyjs_dir=None, pyb2d3=None):
    """create the page dir `out` (pyb2d3: a conda package, default: the local build)"""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    copy_page(out)
    pack_examples(out)
    pyb2d3 = pyb2d3 or local_pyb2d3_build()
    pack_packages(out, [pyb2d3, *fetch_packages(PACKAGES)])
    pyjs_url = copy_pyjs(out, pyjs_dir)

    # the archives pyjs unpacks: the content hash in the file name (a new build is a new
    # url, the url is the cache key of the browser and of pyjs); the size is for the
    # progress bar
    archives = []
    for name, path in (("examples", "/examples"), ("packages", "/")):
        data = (out / f"{name}.tar.gz").read_bytes()
        url = f"{name}-{content_hash(data)}.tar.gz"
        (out / f"{name}.tar.gz").rename(out / url)
        archives.append({"url": url, "path": path, "size": len(data)})

    config = {"pyjs": pyjs_url, "archives": archives}
    (out / "config.json").write_text(json.dumps(config, indent=2))
    return pyb2d3


def content_hash(data):
    return hashlib.sha256(data).hexdigest()[:16]


def copy_page(out):
    """index.html, main.js, editor.js: the modules' urls get their content hashes
    (?v=...): a new build is a new url, no stale module from the browser cache.
    (index.html itself and config.json are revalidated: short-lived / no-cache)"""

    def versioned(text, name, data):
        if f'"./{name}"' not in text:
            raise SystemExit(f'build_page: no "./{name}" to version')
        return text.replace(f'"./{name}"', f'"./{name}?v={content_hash(data)}"')

    editor = (HERE / "editor.js").read_bytes()
    main = versioned((HERE / "main.js").read_text(), "editor.js", editor)
    index = versioned((HERE / "index.html").read_text(), "main.js", main.encode())
    (out / "editor.js").write_bytes(editor)
    (out / "main.js").write_text(main)
    (out / "index.html").write_text(index)


def main():
    """command line"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, help="page directory (recreated)")
    parser.add_argument(
        "--pyjs",
        type=Path,
        help=f"a local pyjs npm package dir (dist/ + assets/), default: pyjs {PYJS_VERSION} from npm",
    )
    parser.add_argument(
        "--pyb2d3",
        type=Path,
        help="the pyb2d3 conda package (.tar.bz2, default: the newest local build of "
        "this version, emscripten_forge/output)",
    )
    args = parser.parse_args()
    build(args.out.resolve(), args.pyjs, args.pyb2d3)
    print(
        f"page written to {args.out}, serve it e.g. with: python -m http.server -d {args.out} 8000"
    )


if __name__ == "__main__":
    main()
