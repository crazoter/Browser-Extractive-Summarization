// if you checked "fancy-settings" in extensionizr.com, uncomment this lines

// var settings = new Store("settings", {
//     "sample_setting": "This is how you use Store.js to remember values"
// });


//example of using a message handler from the inject scripts
// chrome.extension.onMessage.addListener(
//   function(request, sender, sendResponse) {
//   	chrome.pageAction.show(sender.tab.id);
//     sendResponse();
//   });

let summaries = [];
let successes = 0;

// https://stackoverflow.com/questions/32718645/google-chrome-extension-add-the-tab-to-context-menu/32719354#32719354
chrome.contextMenus.create({
  id: "summarize",
  title: "Summarize",
  contexts: ["all"]
});
chrome.contextMenus.create({
  id: "showSummaries",
  title: "showSummaries",
  contexts: ["all"]
});

const display = text => {
  // alert(text);
  chrome.tabs.query({active: true, windowId: chrome.windows.WINDOW_ID_CURRENT}, tabs => {
    chrome.tabs.sendMessage(tabs[0].id, {method: "console.log", data: text}, null)
  });
};

// https://stackoverflow.com/questions/23931605/close-clear-a-chrome-extension-notification-while-notification-panel-is-open
// https://stackoverflow.com/questions/5732031/chrome-extension-development-auto-close-the-notification-box
// open a window to take focus away from notification and there it will close automatically
function openTemporaryWindowToRemoveFocus() {
  var win = window.open("about:blank", "emptyWindow", "width=1, height=1, top=-500, left=-500");
  win.close();
}

const notify = text => {
  display(text);
  // const id = "id" + Math.random().toString();
  // const options = {
  //   title: 'Summarizer',
  //   message: text,
  //   iconUrl: 'icons/icon128.png',
  //   type: 'basic'
  // };
  // chrome.notifications.create(null, options);
  // setTimeout(function () {
  //   chrome.notifications.clear(null, function(wasCleared) {
  //     // openTemporaryWindowToRemoveFocus();
  //   });
  // }, 3000);
  // // alert(JSON.stringify(chrome.runtime.lastError));
};

const displayError = text => {
  alert(text);
}

const requestSummary = async (text) => {
  const url = "http://localhost:5000/summarize";
  const contents = {
    "text": text
  };
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(contents)
  });
  // display(response.status);
  return response.json();
};

const summarize = () => {
  chrome.tabs.query({active: true, windowId: chrome.windows.WINDOW_ID_CURRENT}, tabs => {
    chrome.tabs.sendMessage(tabs[0].id, {method: "getSelection"}, selection => {
      if (selection) {
        notify("Reqesting summary...");
        const idx = summaries.length;
        summaries.push("");
        requestSummary(selection).then(result => {
          // displayError(JSON.stringify(result));
          // if (result) {
          //   // display(result[0].summary_text);
          //   summaries[idx] = result[0].summary_text;
          //   successes++;
          //   notify(`Summarized ${successes}/${summaries.length}`);
          // }
          // else {
          //   displayError("Error occurred");
          // }
        });
      } else {
        displayError("Nothing selected (refresh page?)");
      }
    });
  });
};

const showSummaries = () => {
  for (let i = 0; i < summaries.length; i++) {
    const txt = summaries[i];
    display(txt);
  }
};

chrome.contextMenus.onClicked.addListener(function(info, tab) {
  if (info.menuItemId === "summarize") {
    summarize();
  } else if (info.menuItemId === "showSummaries") {
    showSummaries();
  } 
});

// https://developer.chrome.com/docs/extensions/reference/commands/
chrome.commands.onCommand.addListener((command) => {
  if (command === "summarize") {
    summarize();
  } else if (command === "showSummaries") {
    showSummaries();
  } 
});


