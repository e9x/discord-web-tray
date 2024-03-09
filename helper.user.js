// ==UserScript==
// @name         Discord Web Tray Helper
// @namespace    https://github.com/e9x
// @version      1.0.0
// @description  Client helper for Discord Web Tray
// @author       e9x
// @homepageURL  https://github.com/e9x/discord-web-tray
// @match        https://*.discord.com/app
// @match        https://*.discord.com/channels/*
// @match        https://*.discord.com/login
// @icon         https://www.google.com/s2/favicons?sz=64&domain=discord.com
// @grant        window.close
// @grant        window.focus
// @grant        unsafeWindow
// @run-at       document-start
// ==/UserScript==

const serverPort = 39819;

const serverURL = `ws://127.0.0.1:${serverPort}`;

const pageTitleUpdated = listenPageTitleUpdated();

let reconnect = true;

connectToServer();

function connectToServer() {
  console.log("Connecting to tray...");

  const socket = new WebSocket(serverURL);

  /**
   * @type {boolean|null}
   */
  let lastStatus = null;

  const parseTitle = () => {
    // Parsing logic from WebCord
    // https://github.com/SpacingBat3/WebCord/blob/60faa5ab6cdbcd5e3566734fb0a953951129970e/sources/code/main/windows/main.ts#L324
    if (document.title.includes("|")) {
      // Wrap new title style!
      const sections = document.title.split("|");
      const dirty =
        sections[0]?.includes("•") ?? false
          ? true
          : sections[0]?.includes("(") ?? false
          ? sections[0]?.match(/\(([0-9]+)\)/)?.[1] ?? "m"
          : false;

      // Fetch status for ping and title from current title
      const status = typeof dirty === "string" ? true : dirty ? false : null;

      if (lastStatus === status) return;
      // Set tray icon and taskbar flash

      let icon = "default";
      let flash = false;
      let tooltipSuffix = "";

      switch (status) {
        case true:
          icon = "warn";
          flash = true;
          tooltipSuffix = ` - ${dirty} ${
            dirty === "1" ? "mention" : "mentions"
          }`;
          break;
        case false:
          icon = "unread";
          break;
      }

      socket.send(JSON.stringify({ icon, flash, tooltipSuffix }));

      lastStatus = status;
    }
  };

  pageTitleUpdated.addEventListener("page-title-updated", parseTitle);

  socket.addEventListener("error", (ev) => {
    console.error("socket error", ev);
  });

  socket.addEventListener("open", () => {
    parseTitle();
  });

  socket.addEventListener("message", (ev) => {
    switch (ev.data) {
      case "close":
        window.close();
        reconnect = false;
        break;
      case "toggle":
        if (document.hasFocus()) window.blur();
        else window.focus();
        break;
      default:
        console.warn("Unknown message:", ev.data);
        break;
    }
  });

  socket.addEventListener("close", () => {
    pageTitleUpdated.removeEventListener("page-title-updated", parseTitle);
    // there may be too many clients connected or the close button in the menu was pressed
    console.log("socket closed");
    if (reconnect) setTimeout(() => connectToServer(), 3000);
  });

  return socket;
}

/**
 * imitates electron's page-title-updated event on windows
 * @returns {EventTarget}
 */
function listenPageTitleUpdated() {
  const titleUpdates = new EventTarget();

  const titleDesc = Object.getOwnPropertyDescriptor(
    unsafeWindow.Document.prototype,
    "title"
  );

  // hook title to catch when it updates
  Object.defineProperty(unsafeWindow.Document.prototype, "title", {
    configurable: true,
    enumerable: true,
    get() {
      return titleDesc.get.call(this);
    },
    set(value) {
      titleDesc.set.call(this, value);
      titleUpdates.dispatchEvent(new Event("page-title-updated"));
    },
  });

  return titleUpdates;
}
