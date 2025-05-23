const rasaApiUrl = 'http://localhost:5005/webhooks/rest/webhook'; // REST API Endpunkt
  const chatLog = document.getElementById('chat-log'); //
  const userInput = document.getElementById('user-input'); //

  function appendMessage(sender, message) { //
    const messageDiv = document.createElement('div'); //
    messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message'; //
    messageDiv.textContent = message; //
    chatLog.appendChild(messageDiv); //
    chatLog.scrollTop = chatLog.scrollHeight; // Scrollen zum neuesten Nachricht
  }

  async function sendMessage() { //
    const message = userInput.value.trim(); //
    if (message === '') return; //

    appendMessage('user', message); //
    userInput.value = ''; //

    try {
      const response = await fetch(rasaApiUrl, { //
        method: 'POST', //
        headers: { //
          'Content-Type': 'application/json' //
        },
        body: JSON.stringify({ //
          sender: 'user_id_123', // Eine beliebige Benutzer-ID //
          message: message //
        })
      });

      const data = await response.json(); //

      if (response.ok) { //
        if (data && data.length > 0) { //
          data.forEach(botResponse => { //
            if (botResponse.text) { //
              appendMessage('bot', botResponse.text); //
            }
            // Hier könntest du auch andere Bot-Antworttypen (buttons, image, etc.) verarbeiten
          });
        } else {
          appendMessage('bot', 'Entschuldigung, ich habe das nicht verstanden oder keine passende Antwort.'); //
        }
      } else {
        appendMessage('bot', `Fehler vom Server: ${response.status} ${response.statusText}`); //
        console.error('Server response error:', data); //
      }
    } catch (error) {
      appendMessage('bot', `Verbindungsfehler: ${error.message}`); //
      console.error('Fetch error:', error); //
    }
  }

  // Senden mit Enter-Taste
  userInput.addEventListener('keypress', function(event) { //
    if (event.key === 'Enter') { //
      sendMessage(); //
    }
  });

  // Initialnachricht vom Bot (optional)
  // sendMessage('Hallo'); // Dies würde eine leere Nachricht an Rasa senden, um die Begrüßung zu erhalten.
  // Eine bessere Methode wäre, eine "init_payload" zu senden, wie es Rasa Webchat macht.
  // Für diesen Minimal-Bot müsstest du "Hallo" eingeben, um den Bot zu begrüßen.