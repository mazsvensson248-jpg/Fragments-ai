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

  // Show loading message
  const generateBtn = document.querySelector('button[onclick="generateVideos()"]');
  const originalText = generateBtn.textContent;
  generateBtn.textContent = '🎬 Starting Generation...';
  generateBtn.disabled = true;

  // Start video generation
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
  .then(res => {
    if (!res.ok) throw new Error("Server error");
    return res.json();
  })
  .then(data => {
    if (data.status === "started") {
      alert("✅ Video generation started! This will take 3-5 minutes. Please wait...");
      
      // Start polling for status
      pollVideoStatus(data.session_id, generateBtn, originalText);
    } else {
      throw new Error(data.message || "Unknown error");
    }
  })
  .catch(err => {
    alert("❌ Failed to start video generation: " + err.message);
    generateBtn.textContent = originalText;
    generateBtn.disabled = false;
  });
}

function pollVideoStatus(sessionId, button, originalText) {
  const statusInterval = setInterval(() => {
    fetch(`/api/status/${sessionId}`)
      .then(res => res.json())
      .then(status => {
        console.log('Status:', status);
        
        // Update button text with progress
        if (status.progress !== undefined) {
          button.textContent = `🎬 ${status.step} (${status.progress}%)`;
        } else {
          button.textContent = `🎬 ${status.step || 'Processing...'}`;
        }
        
        if (status.status === 'completed') {
          clearInterval(statusInterval);
          button.textContent = '📥 Downloading...';
          
          // Start download
          const downloadUrl = `/download/${sessionId}`;
          const a = document.createElement("a");
          a.href = downloadUrl;
          a.download = `fragments_ai_video.mp4`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          
          alert("✅ Video generated and downloaded successfully!");
          
          // Reset button
          button.textContent = originalText;
          button.disabled = false;
          
        } else if (status.status === 'failed') {
          clearInterval(statusInterval);
          alert("❌ Video generation failed: " + (status.error || "Unknown error"));
          
          // Reset button
          button.textContent = originalText;
          button.disabled = false;
        }
        // If still processing, continue polling
      })
      .catch(err => {
        console.error('Status check failed:', err);
        // Continue polling even if one request fails
      });
  }, 2000); // Check every 2 seconds
  
  // Safety timeout after 10 minutes
  setTimeout(() => {
    clearInterval(statusInterval);
    if (button.disabled) {
      alert("⏰ Video generation is taking longer than expected. Please try again.");
      button.textContent = originalText;
      button.disabled = false;
    }
  }, 600000); // 10 minutes
}
