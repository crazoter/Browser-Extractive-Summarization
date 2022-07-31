// https://stackoverflow.com/questions/21359605/window-getselection-returning-undefined-or-null
chrome.runtime.onMessage.addListener( 
  function(request, sender, sendResponse) { 
    if (request.method == "getSelection") {
      const result = window.getSelection().toString();
      sendResponse(result);
    } else if (request.method == "console.log") {
      console.log(request.data);
    }
  }
);