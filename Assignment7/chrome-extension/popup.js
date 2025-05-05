const backendUrl = "http://127.0.0.1:5000"; // Change to your backend URL

document.getElementById('extractBtn').addEventListener('click', async () => {
    document.getElementById('status').textContent = "Extracting...";
    let [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    // Ask background.js if this URL is blacklisted
    chrome.runtime.sendMessage(
      { action: "checkBlacklist", url: tab.url },
      (response) => {
        if (response.isBlacklisted) {
          document.getElementById('status').textContent = "This site is blacklisted.";
        } else {
          chrome.scripting.executeScript({
            target: {tabId: tab.id},
            files: ['content.js']
          });
        }
      }
    );
  });

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("Received message:", request);
  if (request.action === "sendHtmlToBackend") {
    fetch(`${backendUrl}/extract`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: request.url, html: request.html})
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById('status').textContent = "Extracted and sent!";
    })
    .catch(err => {
      document.getElementById('status').textContent = "Error sending data.";
    });
  }
});

document.getElementById('searchBtn').addEventListener('click', () => {
  const query = document.getElementById('searchInput').value;
  document.getElementById('status').textContent = "Searching...";
  fetch(`${backendUrl}/search`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({query})
  })
  .then(res => res.json())
  .then(data => {
    console.log("Search response:", data);
    const results = document.getElementById('results');
    results.innerHTML = "";
    if (!data.results || data.results.length === 0) {
      const li = document.createElement('li');
      li.textContent = "No results found.";
      results.appendChild(li);
    } else {
      data.results.forEach(result => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="#">${result.url}</a><br><small>${result.chunk.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</small>`;
        li.querySelector('a').addEventListener('click', (e) => {
          e.preventDefault();
          // Open the URL in a new tab and pass the chunk to highlight
          chrome.tabs.create({ url: result.url }, (tab) => {
            // Wait for the tab to load, then inject the highlight script
            chrome.scripting.executeScript({
              target: { tabId: tab.id },
              func: highlightText,
              args: [result.chunk]
            });
          });
        });
        results.appendChild(li);
      });
    }
    document.getElementById('status').textContent = "";
  })
  .catch(err => {
    document.getElementById('status').textContent = "Error searching.";
  });
});

// Highlight function to be injected
function highlightText(text) {
  // Escape regex special characters
  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  const bodyText = document.body.innerHTML;
  const safeText = escapeRegExp(text.trim());
  const regex = new RegExp(safeText, 'gi');
  document.body.innerHTML = bodyText.replace(regex, match => `<mark style="background: yellow;">${match}</mark>`);
}