(() => {
  const supportedHosts = new Set([
    "shikimori.one", "www.shikimori.one",
    "shikimori.me", "www.shikimori.me",
    "shikimori.org", "www.shikimori.org"
  ]);

  function readTitle() {
    if (!supportedHosts.has(location.hostname)) return null;

    const match = location.pathname.match(/^\/(animes|mangas)\/(\d+)(?:-|\/|$)/);
    if (!match) return null;

    const [, pathType, id] = match;
    const titleElement = document.querySelector("h1");
    const title = titleElement?.textContent?.trim() || document.title.replace(/\s*[|–—-]\s*Shikimori.*$/i, "").trim();
    if (!title) return null;

    const poster = document.querySelector(
      ".c-image img, .b-db_entry img, img[itemprop='image'], .poster img, .cover img, meta[property='og:image']"
    );
    const image = poster?.getAttribute("content")
      || poster?.currentSrc
      || poster?.getAttribute("data-src")
      || poster?.getAttribute("src")
      || null;

    const text = document.body?.innerText || "";
    const yearMatch = text.match(/(?:Год|Year|Дата выхода|Aired|Published)\s*:?\s*(?:\D{0,15})((?:19|20)\d{2})/i);
    const countMatch = pathType === "animes"
      ? text.match(/(?:Эпизоды|Серии|Episodes)\s*:?\s*(\d+)/i)
      : text.match(/(?:Главы|Chapters)\s*:?\s*(\d+)/i);

    return {
      source: "shikimori",
      externalId: id,
      mediaType: pathType === "animes" ? "anime" : "manga",
      title,
      url: location.href,
      image: image ? new URL(image, location.href).href : null,
      year: yearMatch ? Number(yearMatch[1]) : null,
      totalCount: countMatch ? Number(countMatch[1]) : null
    };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "OTAKURATE_GET_TITLE") {
      sendResponse({ title: readTitle() });
    }
    return true;
  });

  function publishCurrentTitle() {
    const title = readTitle();
    if (title) {
      chrome.storage.local.set({ currentShikimoriTitle: title });
    } else {
      chrome.storage.local.remove("currentShikimoriTitle");
    }
  }

  publishCurrentTitle();

  // Shikimori can navigate between entries without a full page reload.
  let lastUrl = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      publishCurrentTitle();
    }
  });
  if (document.documentElement) {
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }
})();