(function () {
  function setLoadingState() {
    var bar = document.getElementById("global-loading-bar");
    if (!bar) return;

    var hasLoadingNode = document.querySelector('[data-dash-is-loading="true"]') !== null;
    if (hasLoadingNode) {
      bar.classList.add("active");
    } else {
      bar.classList.remove("active");
    }
  }

  function initObserver() {
    setLoadingState();

    var observer = new MutationObserver(function () {
      setLoadingState();
    });

    observer.observe(document.body, {
      attributes: true,
      childList: true,
      subtree: true,
      attributeFilter: ["data-dash-is-loading"],
    });

    document.addEventListener("visibilitychange", setLoadingState);
    window.addEventListener("focus", setLoadingState);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initObserver);
  } else {
    initObserver();
  }
})();
