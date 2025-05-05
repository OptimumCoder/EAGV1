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
    const results = document.getElementById('results');
    results.innerHTML = "";
    if (!data.urls || data.urls.length === 0) {
      const li = document.createElement('li');
      li.textContent = "No results found.";
      results.appendChild(li);
    } else {
      data.urls.forEach(url => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="${url}" target="_blank">${url}</a>`;
        results.appendChild(li);
      });
    }
    document.getElementById('status').textContent = "";
  })
  .catch(err => {
    document.getElementById('status').textContent = "Error searching.";
  });
});