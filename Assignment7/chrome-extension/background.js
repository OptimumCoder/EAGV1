// List of blacklisted domains
const blacklist = [
  "gmail.com",
  "web.whatsapp.com"
];

// Listen for messages from popup.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkBlacklist") {
    const url = new URL(request.url);
    const isBlacklisted = blacklist.some(domain => url.hostname.includes(domain));
    sendResponse({ isBlacklisted });
  }
  // Return true to indicate async response if needed
  return true;
});