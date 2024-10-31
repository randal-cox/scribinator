function toHHMMSS(seconds) {
    seconds = Math.round(seconds);
    const hh = Math.floor(seconds / 3600);
    const mm = Math.floor((seconds % 3600) / 60);
    const ss = seconds % 60;

    // Pads zero when needed (e.g., "07" instead of "7")
    return [hh, mm, ss].map(number => String(number).padStart(2, '0')).join(':');
}
function update_results(event) {
  // copy the source results
  let resultsCopy = {...document.transcriptionator.results};

  // TODO: fill in any changes in the meta

  // fill in any changes in the transcript
  let segments = resultsCopy.segments;
  for (let i = 0; i < segments.length; i++) {
    let segment = segments[i];
    let e = document.getElementById(`transcript-${segment.segment}`);
    if (e) {
      let textareaContent = e.value;
      segments[i].transcript = textareaContent;
    }
    // TODO: should allow for changes to who is speaking
  }

  // 3. Convert to a pretty printed JSON string
  let prettyPrintedJson = JSON.stringify(resultsCopy, null, 2);

  // 4. Put it in the "results" element
  let resultElement = document.getElementById('results');
  resultElement.innerText = prettyPrintedJson;
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}
function populateTranscript() {
  // fetch speakers element
  let speakersElement = document.getElementById('speakers_all');

  // return if speakersElement is null
  if (!speakersElement) {
    console.error('Element with id "speakers" not found');
    return;
  }

  // trim and separate speakers by comma
  let speakers = speakersElement.value.split(',').map(e => e.trim());

  // check if document.transcriptionator.results is defined and contains 'segments'
  if (!(document.transcriptionator.results && document.transcriptionator.results['segments'])) {
    console.error('Document transcriptionator results segments not found');
    return;
  }

  // define emotion abbreviations and full names
  let emotionsFull = ['fear', 'contempt', 'disgust', 'sadness', 'anger', 'happiness', 'surprise'];
  let emotionsShort = ['f', 'c', 'd', 's', 'a', 'h', '!'];

  // fetch segments from results
  let segments = document.transcriptionator.results['segments'];

  // start the result string with the opening table tag
  let result = '<table id="transcript" width="100%">';

  // iterate over each segment
  segments.forEach((segment) => {
    // Skip if transcript is empty
    if (!segment.transcript.trim()) {
      return;
    }

    let timeStamp =  toHHMMSS(segment.start)

    // fetch speaker's name using the index
    let speakerName = speakers[segment.speaker];

    // fetch the highestEmotion's full name using the emotion index
    let highestEmotion = emotionsFull[segment.emotion];

    let allEmotions = segment.emotions.map((emotion, idx) => {
      return `<span class="tooltip-container">${emotionsShort[idx]}<span class="tooltip-text" data-tooltip="${emotionsFull[idx]}"></span></span>` + emotion;
    }).join(", ");

    // create a new row for the table
    let segmentResult =   `<tr>
                                    <td>
                                        <div style="display: flex; justify-content: space-between;">
                                            <div>
                                                <strong>${speakerName}</strong> @ ${timeStamp} | <b>${highestEmotion}</b> [${allEmotions}]    
                                            </div> 
                                            <div class="indent">
                                                <audio controls><source src="${segment.path_audio}" type="audio/mp3"></audio>
                                            </div>  
                                        </div>
                                        <div class="indent">
                                            <textarea id="transcript-${segment.segment}" style="display:block; width:100%;">${segment.transcript}</textarea>
                                        </div>
                                    </td>
                                </tr>`

    // add the new row to the result string
    result += segmentResult;
  });

  // close the table tag in the result string
  result += '</table>';

  // fetch the transcript div
  let transcriptDiv = document.getElementById('transcript');

  // set the result string as the innerHTML of the transcriptDiv
  if (transcriptDiv) {
    transcriptDiv.innerHTML = result;


    segments.forEach((segment) => {
      let textarea = document.getElementById(`transcript-${segment.segment}`);
      if (textarea) {
        textarea.addEventListener('input', update_results);
        textarea.addEventListener('change', update_results);
        autoResizeTextarea(textarea);
      }
    });


  } else {
    console.error('Element with id "transcript" not found');
  }
}


document.addEventListener("DOMContentLoaded", function() {
  // pretty-print the original results in the debug text area
  let prettyPrinted = JSON.stringify(document.transcriptionator.results, null, 2);
  document.getElementById('debug').value = prettyPrinted;

  // Fill in the page title
  document.title = `${document.transcriptionator.results.title} - Transcriptionator`;

  // Fill in table of meta information
  let keys = ["description", "location", "date", "speakers_all", "title"];
  for (let key of keys) {
    // Get the DOM element by ID
    let element = document.getElementById(key);
    if(element) {
      element.value = document.transcriptionator.results[key];
      element.addEventListener('change', populateTranscript);
    }
  }

  document.getElementById('resultsShowButton').addEventListener('click', function() {
    let resultsElement = document.getElementById('results');
    let buttonElement = document.getElementById('resultsShowButton');

    if (resultsElement.style.display === "none") {
      // If results are not displayed, show them and change button text
      resultsElement.style.display = "block";
      buttonElement.innerText = "Hide";
    } else {
      // If results are already displayed, hide them and change button text
      resultsElement.style.display = "none";
      buttonElement.innerText = "Show";
    }
  });

  document.getElementById('resultsDownloadButton').addEventListener('click', function() {
    let textToDownload = document.getElementById('results').innerText;

    // Create a blob out of the text
    let blob = new Blob([textToDownload], {type: 'application/json'});

    // Create a link element
    let a = document.createElement("a");

    // Assign the blob URL to the link element
    a.href = URL.createObjectURL(blob);

    // Set the file name
    a.download = "cache.js";

    // Append it to the body and perform a click to initiate download
    document.body.appendChild(a); // Required for Firefox
    a.click();
    setTimeout(function() { // Removed after initiating download to avoid memory leaks
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    }, 0);
  });

  document.getElementById('resultsCopyButton').addEventListener('click', function() {
    let textToCopy = document.getElementById('results').innerText;
    navigator.clipboard.writeText(textToCopy).then(function() {
      console.log('Copying to clipboard was successful!');
    }, function(err) {
      console.error('Could not copy text: ', err);
    });
  });

  document.getElementById('finalShowButton').addEventListener('click', function() {
    let resultsElement = document.getElementById('final');
    let buttonElement = document.getElementById('finalShowButton');

    if (resultsElement.style.display === "none") {
      // If results are not displayed, show them and change button text
      resultsElement.style.display = "block";
      buttonElement.innerText = "Hide";
    } else {
      // If results are already displayed, hide them and change button text
      resultsElement.style.display = "none";
      buttonElement.innerText = "Show";
    }
  });

  document.getElementById('finalDownloadButton').addEventListener('click', function() {
    let textToDownload = document.getElementById('final').innerText;

    // Create a blob out of the text
    let blob = new Blob([textToDownload], {type: 'application/json'});

    // Create a link element
    let a = document.createElement("a");

    // Assign the blob URL to the link element
    a.href = URL.createObjectURL(blob);

    // Set the file name
    a.download = "transcript.txt";

    // Append it to the body and perform a click to initiate download
    document.body.appendChild(a); // Required for Firefox
    a.click();
    setTimeout(function() { // Removed after initiating download to avoid memory leaks
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    }, 0);
  });

  document.getElementById('finalCopyButton').addEventListener('click', function() {
    let textToCopy = document.getElementById('final').innerText;
    navigator.clipboard.writeText(textToCopy).then(function() {
      console.log('Copying to clipboard was successful!');
    }, function(err) {
      console.error('Could not copy text: ', err);
    });
  });


  populateTranscript()
  update_results()

});


