export function startListening() {
  const recognition = new webkitSpeechRecognition();

  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'uk-UA'; // або uk-UA

  recognition.onresult = (event) => {
    const text = event.results[event.results.length - 1][0].transcript;

    console.log('heard:', text);

    // 🔥 ключове слово
    if (text.toLowerCase().includes('edit', 'едіт', 'едит')) {
      activateAssistant();
    }
  };

  recognition.start();
}
