function generateVideos() {
  const prompt = document.getElementById('prompt').value.trim();
  const selectedVideos = [...document.querySelectorAll('.video-item input:checked')].map(cb => cb.value);

  if (!prompt) {
    alert('Please enter a prompt!');
    return;
  }

  if (selectedVideos.length === 0 || selectedVideos.length > 10) {
    alert('Please select between 1 and 10 videos.');
    return;
  }

  fetch("/api/video", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      prompt: prompt,
      links: selectedVideos
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message) {
      alert("✅ " + data.message);
    } else {
      alert("⚠️ Unexpected response from server.");
    }
  })
  .catch(err => {
    console.error(err);
    alert("❌ Failed to contact server.");
  });
}
