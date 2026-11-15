// Sample gallery -> the sandbox in the browser (<docs root>/sandbox/, built by
// conf.py from examples/web). Every tile has an
// <a class="pyb2d3-sandbox-link" data-sample="Category/Name">; this sets its href
// relative to the docs root (the gallery is included on pages of different
// depths) and makes the tile's video open the same link.
document.addEventListener("DOMContentLoaded", () => {
  const root = new URL(document.documentElement.dataset.content_root || "./", location.href);
  for (const link of document.querySelectorAll("a.pyb2d3-sandbox-link[data-sample]")) {
    const url = new URL("sandbox/index.html", root);
    url.searchParams.set("sample", link.dataset.sample);
    link.href = url.href;
    link.title = `run ${link.dataset.sample} in the browser`;
    const tile = link.closest(".sd-col") || link.parentElement;
    const video = tile && tile.querySelector("video");
    if (video) {
      video.style.cursor = "pointer";
      video.title = link.title;
      video.addEventListener("click", () => { location.href = link.href; });
    }
  }
});
