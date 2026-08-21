(() => {
  "use strict";
  const STATE_KEY = "__adOverlayUnlockState__", MARKER = "data-ad-overlay-unlock-hidden", ROOT_MARKER = "data-ad-overlay-unlock-root";
  const SIGNAL = /(?:^|[-_\s/.:])(?:ad|ads|advert(?:isement|ising)?|sponsor(?:ed)?|promo(?:tional)?|interstitial|paywall)(?:$|[-_\s/.:])|広告|スポンサー|プロモーション/i;
  const VETO = /(?:login|sign[ -]?in|auth|account|password|checkout|payment|purchase|billing|card|verify|captcha|consent|cookie|privacy|ログイン|認証|パスワード|決済|支払|購入|クッキー)/i;
  const MAX_HIDDEN = 12, MAX_QUEUED_NODES = 80, MAX_SCANNED_ELEMENTS = 2_400, INITIAL_CHUNK_SIZE = 80, DEBOUNCE_MS = 120, MONITOR_MS = 8_000;
  if (window.top !== window) return;
  const previous = window[STATE_KEY];
  if (previous) { restore(previous); delete window[STATE_KEY]; return; }
  const state = { active: true, changes: [], roots: [], observer: null, queue: new Set(), debounceTimer: 0, animationFrame: 0, initialFrame: 0, scrollFrame: 0, expiryTimer: 0, hiddenCount: 0, initialScannedCount: 0, mutationScannedCount: 0, fixedScrollCompensated: false };
  window[STATE_KEY] = state;
  startInitialScan();
  startObserver();

  function propertySnapshot(element, properties) { return properties.map((property) => ({ property, value: element.style.getPropertyValue(property), priority: element.style.getPropertyPriority(property) })); }
  function setManagedProperties(element, changes, destination) {
    const snapshot = propertySnapshot(element, changes.map(({ property }) => property));
    for (const { property, value, priority = "important" } of changes) element.style.setProperty(property, value, priority);
    destination.push({ element, snapshot, changes });
  }
  function restorePropertyChanges(entries) {
    for (const { element, snapshot, changes } of entries) {
      if (!element.isConnected) continue;
      for (const original of snapshot) {
        const applied = changes.find(({ property }) => property === original.property);
        if (element.style.getPropertyValue(original.property) !== applied.value || element.style.getPropertyPriority(original.property) !== (applied.priority || "important")) continue;
        if (original.value) element.style.setProperty(original.property, original.value, original.priority); else element.style.removeProperty(original.property);
      }
    }
  }
  function stop(activeState) {
    activeState.active = false; activeState.observer?.disconnect();
    if (activeState.debounceTimer) clearTimeout(activeState.debounceTimer);
    if (activeState.animationFrame) cancelAnimationFrame(activeState.animationFrame);
    if (activeState.initialFrame) cancelAnimationFrame(activeState.initialFrame);
    if (activeState.scrollFrame) cancelAnimationFrame(activeState.scrollFrame);
    if (activeState.expiryTimer) clearTimeout(activeState.expiryTimer);
    activeState.queue.clear();
  }
  function restore(activeState) {
    stop(activeState); restorePropertyChanges(activeState.changes);
    for (const { element } of activeState.changes) if (element.isConnected) element.removeAttribute(MARKER);
    restorePropertyChanges(activeState.roots);
    for (const { element } of activeState.roots) if (element.isConnected) element.removeAttribute(ROOT_MARKER);
  }
  function startObserver() {
    state.observer = new MutationObserver((records) => {
      if (!state.active || state.hiddenCount >= MAX_HIDDEN || state.mutationScannedCount >= MAX_SCANNED_ELEMENTS) return;
      for (const record of records) {
        if (record.type === "attributes") addToQueue(record.target);
        for (const node of record.addedNodes) if (node.nodeType === Node.ELEMENT_NODE) addToQueue(node);
      }
      scheduleFlush();
    });
    state.observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "style", "hidden", "open", "aria-modal", "aria-hidden", "role", "id", "src", "data-anchor-status", "data-anchor-shown", "data-ad-status"] });
    state.expiryTimer = setTimeout(() => stop(state), MONITOR_MS);
    addEventListener("pagehide", () => stop(state), { once: true });
  }
  function addToQueue(element) { if (state.queue.size < MAX_QUEUED_NODES) state.queue.add(element); }
  function scheduleFlush() {
    if (state.debounceTimer || state.animationFrame || !state.queue.size) return;
    state.debounceTimer = setTimeout(() => {
      state.debounceTimer = 0;
      state.animationFrame = requestAnimationFrame(() => {
        state.animationFrame = 0;
        const queued = [...state.queue]; state.queue.clear();
        for (const element of queued) { scan(element); if (!state.active || state.hiddenCount >= MAX_HIDDEN || state.mutationScannedCount >= MAX_SCANNED_ELEMENTS) break; }
      });
    }, DEBOUNCE_MS);
  }
  function startInitialScan() {
    const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_ELEMENT);
    const runChunk = () => {
      state.initialFrame = 0;
      if (!state.active) return;
      let processed = 0;
      while (processed < INITIAL_CHUNK_SIZE && state.initialScannedCount < MAX_SCANNED_ELEMENTS && state.hiddenCount < MAX_HIDDEN) {
        const element = walker.nextNode();
        if (!element) return;
        state.initialScannedCount += 1;
        consider(element);
        processed += 1;
      }
      if (state.active && state.initialScannedCount < MAX_SCANNED_ELEMENTS && state.hiddenCount < MAX_HIDDEN) state.initialFrame = requestAnimationFrame(runChunk);
    };
    state.initialFrame = requestAnimationFrame(runChunk);
  }
  function scan(root) {
    if (!state.active || !root?.isConnected) return;
    const selector = "iframe, [id], [class], [role], [aria-label], [data-testid], [style*='position']";
    const inspect = (element) => {
      if (state.hiddenCount >= MAX_HIDDEN || state.mutationScannedCount >= MAX_SCANNED_ELEMENTS) return false;
      state.mutationScannedCount += 1;
      if (element instanceof HTMLElement && element.matches(selector)) consider(element);
      return state.hiddenCount < MAX_HIDDEN && state.mutationScannedCount < MAX_SCANNED_ELEMENTS;
    };
    if (!inspect(root)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
    for (let element = walker.nextNode(); element; element = walker.nextNode()) if (!inspect(element)) return;
  }
  function consider(element) {
    // AdSense anchors are intentionally handled separately: their small fixed
    // banner does not imply that the document's scrolling has been locked.
    if (isGoogleAdSenseAnchorAd(element)) { hide(element); return; }
    if (isOverlayCandidate(element)) { hide(element); unlockRoots(); }
  }
  function protectedEvidence(element, includeText) {
    return [element.id, element.className, element.getAttribute("aria-label"), element.getAttribute("role"), includeText ? (element.innerText || element.textContent || "").slice(0, 1_200) : ""].filter((value) => typeof value === "string").join(" ");
  }
  function hasProtectedGoogleGateContext(element, gateRoot) {
    for (let current = element; current instanceof HTMLElement; current = current.parentElement) {
      if (VETO.test(protectedEvidence(current, true)) || current.matches("form, input[type='password']") || current.querySelector("form, input[type='password']")) return true;
      if (current === gateRoot) return false;
    }
    return true;
  }
  function isFundingChoicesRewardedGate(element) {
    if (!element.matches(".fc-message-root .fc-monetization-dialog-container, .fc-message-root .fc-dialog-overlay")) return false;
    const gateRoot = element.closest(".fc-message-root");
    return Boolean(gateRoot?.querySelector(".fc-monetization-dialog-container .fc-rewarded-ad-button")) && !hasProtectedGoogleGateContext(element, gateRoot);
  }
  function isGoogleAdSenseFullscreenAd(element) {
    return element.matches("ins.adsbygoogle.adsbygoogle-noablate[data-vignette-loaded], ins.adsbygoogle.adsbygoogle-noablate[data-slotcar-rewarded]");
  }
  function isGoogleAdSenseAnchorAd(element) {
    if (!(element instanceof HTMLElement) || !element.matches("ins.adsbygoogle.adsbygoogle-noablate[data-anchor-status='displayed'][data-anchor-shown='true']")) return false;
    const style = getComputedStyle(element);
    if (style.position !== "fixed" || style.display === "none" || style.visibility === "hidden" || Number.parseFloat(style.opacity) === 0) return false;
    const anchoredToEdge = style.top !== "auto" || style.bottom !== "auto";
    const zIndex = Number.parseInt(style.zIndex, 10);
    const rect = element.getBoundingClientRect();
    return anchoredToEdge && Number.isFinite(zIndex) && zIndex >= 1_000 && rect.width > 0 && rect.height > 0;
  }
  function coversViewport(rect) {
    const coveredWidth = Math.max(0, Math.min(rect.right, innerWidth) - Math.max(rect.left, 0));
    const coveredHeight = Math.max(0, Math.min(rect.bottom, innerHeight) - Math.max(rect.top, 0));
    return coveredWidth * coveredHeight >= innerWidth * innerHeight * 0.70 && coveredWidth >= innerWidth * 0.75 && coveredHeight >= innerHeight * 0.70;
  }
  function hasProtectedUi(candidate) {
    const protectedElements = document.querySelectorAll("dialog[open], [role='dialog'], [aria-modal='true'], form, input[type='password']");
    for (const element of protectedElements) {
      const style = getComputedStyle(element); if (style.display === "none" || style.visibility === "hidden") continue;
      const text = `${element.getAttribute("aria-label") || ""} ${element.id} ${element.className || ""} ${(element.innerText || "").slice(0, 300)}`;
      const protectedUi = element.matches("dialog[open], [role='dialog'], [aria-modal='true'], input[type='password']") || VETO.test(text);
      if (protectedUi && relatedToProtectedUi(candidate, element)) return true;
    }
    return false;
  }
  function relatedToProtectedUi(candidate, protectedElement) {
    if (candidate.contains(protectedElement) || protectedElement.contains(candidate)) return true;
    const candidateRect = candidate.getBoundingClientRect(), protectedRect = protectedElement.getBoundingClientRect();
    const overlapWidth = Math.max(0, Math.min(candidateRect.right, protectedRect.right) - Math.max(candidateRect.left, protectedRect.left));
    const overlapHeight = Math.max(0, Math.min(candidateRect.bottom, protectedRect.bottom) - Math.max(candidateRect.top, protectedRect.top));
    return overlapWidth * overlapHeight >= Math.min(candidateRect.width * candidateRect.height, protectedRect.width * protectedRect.height) * 0.25;
  }
  function isOverlayCandidate(element) {
    if (!(element instanceof HTMLElement) || element.hasAttribute(MARKER) || element.closest(`[${MARKER}]`)) return false;
    const style = getComputedStyle(element); if (!["fixed", "absolute", "sticky"].includes(style.position) || style.display === "none" || style.visibility === "hidden") return false;
    const rect = element.getBoundingClientRect();
    if (!coversViewport(rect)) return false;
    // Funding Choices embeds a role=dialog advertisement. Its narrowly identified
    // rewarded gate is the sole exception to the general dialog/form safety veto.
    if (isFundingChoicesRewardedGate(element)) return obstructsViewport(element, rect);
    const evidence = [element.id, element.className, element.getAttribute("aria-label"), element.getAttribute("data-testid"), element.getAttribute("src"), element.getAttribute("href"), element.tagName === "IFRAME" ? element.src : "", (element.innerText || element.textContent || "").slice(0, 600)].filter((value) => typeof value === "string").join(" ");
    return (isGoogleAdSenseFullscreenAd(element) || SIGNAL.test(evidence)) && !VETO.test(evidence) && !hasProtectedUi(element) && obstructsViewport(element, rect);
  }
  function obstructsViewport(element, rect) {
    const points = [[innerWidth / 2, innerHeight / 2], [innerWidth * 0.2, innerHeight * 0.2], [innerWidth * 0.8, innerHeight * 0.8]];
    return points.filter(([x, y]) => x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom).filter(([x, y]) => document.elementsFromPoint(x, y).some((hit) => hit === element || element.contains(hit))).length >= 2;
  }
  function hide(element) { setManagedProperties(element, [{ property: "display", value: "none" }], state.changes); element.setAttribute(MARKER, ""); state.hiddenCount += 1; }
  function unlockRoots() {
    for (const root of [document.documentElement, document.body].filter(Boolean)) {
      if (root.hasAttribute(ROOT_MARKER)) continue;
      const style = getComputedStyle(root), fixed = style.position === "fixed", locked = ["hidden", "clip"].includes(style.overflowY) || style.touchAction === "none" || fixed;
      if (!locked) continue;
      const changes = [];
      if (["hidden", "clip"].includes(style.overflowY)) changes.push({ property: "overflow-y", value: "auto" });
      if (style.touchAction === "none") changes.push({ property: "touch-action", value: "auto" });
      if (fixed) {
        const top = Number.parseFloat(style.top);
        changes.push({ property: "position", value: "static" }, { property: "top", value: "auto" }, { property: "left", value: "auto" }, { property: "right", value: "auto" }, { property: "bottom", value: "auto" }, { property: "width", value: "auto" });
        if (!state.fixedScrollCompensated && Number.isFinite(top) && top < 0) {
          state.fixedScrollCompensated = true;
          state.scrollFrame = requestAnimationFrame(() => {
            state.scrollFrame = 0;
            if (state.active) scrollBy(0, -top);
          });
        }
      }
      if (parseFloat(style.maxHeight) <= innerHeight || parseFloat(style.height) <= innerHeight) changes.push({ property: "max-height", value: "none" }, { property: "height", value: "auto" });
      if (!changes.length) continue;
      setManagedProperties(root, changes, state.roots); root.setAttribute(ROOT_MARKER, "");
    }
  }
})();
