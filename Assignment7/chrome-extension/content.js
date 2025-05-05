(function() {
    // Extract all visible text from the page
    // function getText() {
    //   return document.body.innerText;
    // }

    function getHtml() {
        return document.documentElement.outerHTML;
    }
    chrome.runtime.sendMessage({
      action: "sendHtmlToBackend",
      url: window.location.href,
      html: getHtml()
    });
    console.log("content.js end")
  })();