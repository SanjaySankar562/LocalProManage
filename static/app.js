// Browser-side wiring for the two demo features.
const $ = id => document.getElementById(id);

// Send JSON to a FastAPI endpoint and turn HTTP/API errors into readable text.
async function post(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const body = await response.text();
    let error;
    try {
      error = JSON.parse(body);
    } catch {
      throw new Error(`Request failed (${response.status}): ${response.statusText}`);
    }
    const message = Array.isArray(error.detail) ? error.detail.map(item => item.msg).join("; ") : error.detail || response.statusText;
    throw new Error(message);
  }
  return response.json();
}

// Populate the store selector from the server's location data.
fetch("/locations")
  .then(response => response.json())
  .then(locations => {
    $("loc").innerHTML = locations
      .map(location => `<option value="${location.id}">${location.name} (${location.city})</option>`)
      .join("");
  });

// Ask RAG about the selected store and show the supporting passages.
async function ask() {
  $("answer").textContent = "Thinking...";
  try {
    const data = await post("/chat", {
      question: $("q").value,
      location: $("loc").value,
    });
    $("answer").textContent = data.answer +
      (data.sources.length
        ? "\n\nSources:\n- " + data.sources.map(source => source.text).join("\n- ")
        : "");
  } catch (error) {
    $("answer").textContent = "Error: " + error.message;
  }
}

// Draft a review reply and mark negative replies for human approval.
async function reply() {
  $("reply").textContent = "Drafting...";
  try {
    const data = await post("/review-reply", {
      review: $("rev").value,
      rating: Number($("stars").value),
      location: $("loc").value,
    });

    $("reply").textContent = "";
    const replyText = document.createElement("div");
    replyText.textContent = data.reply;
    $("reply").appendChild(replyText);

    const sentiment = document.createElement("div");
    sentiment.textContent = "Sentiment: " + data.sentiment;
    $("reply").appendChild(sentiment);

    if (data.needs_human_approval) {
      const warning = document.createElement("div");
      warning.className = "warn";
      warning.textContent = "A person must approve this reply before it is posted.";
      $("reply").appendChild(warning);
    }
  } catch (error) {
    $("reply").textContent = "Error: " + error.message;
  }
}

// Bind actions after the external script has loaded with the page.
$("ask-button").addEventListener("click", ask);
$("reply-button").addEventListener("click", reply);
