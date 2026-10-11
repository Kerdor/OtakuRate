(() => {
  const match = location.pathname.match(/^\/(animes|mangas)\/(\d+)(?:-|\/|$)/);
  if (!match) {
    chrome.storage.local.remove("currentShikimoriTitle");
    return;
  }

  const [, pathType, id] = match;
  const titleElement = document.querySelector("h1");
  const title = titleElement?.textContent?.trim() || document.title.trim();

  const poster = document.querySelector(
    ".c-image img, .b-db_entry img, img[itemprop='image'], .poster img, .cover img"
  );

  const text = document.body.innerText || "";
  const yearMatch = text.match(/(?:Год|Year|Дата выхода|Aired|Published)\s*:?\s*(?:\D{0,15})((?:19|20)\d{2})/i);
  const countMatch = pathType === "animes"
    ? text.match(/(?:Эпизоды|Серии|Episodes)\s*:?\s*(\d+)/i)
    : text.match(/(?:Главы|Chapters)\s*:?\s*(\d+)/i);

  const titleData = {
    source: "shikimori",
    externalId: id,
    mediaType: pathType === "animes" ? "anime" : "manga",
    title,
    url: location.href,
    image: poster?.src || poster?.getAttribute("data-src") || null,
    year: yearMatch ? Number(yearMatch[1]) : null,
    totalCount: countMatch ? Number(countMatch[1]) : null
  };

  chrome.storage.local.set({ currentShikimoriTitle: titleData });
})();
