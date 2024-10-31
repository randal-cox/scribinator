# Transcriptionator 1000
Transcriptionator is a tool to do transcription and annotation 
of audio files in a completely local manner. It captures
who is speaking, when, what they are saying (in whatever language)
and then annotates this with the seven primary Ekman emotions (fear, 
contempt, disgust, sadness, anger, happiness, and surprise)

The result is editable in a local web page. In this UI, you can 
set the names of the speakers, edit transcription errors, and add
in meta-information about the transcript. To support this, the UI
gives you playback of the entire audio as well as the clips of each
speaker's turn speaking. 

# Installation
- clone repo
- install ffmpeg
- ./bin/setup

# Running transcriptionator
## Command line
transcriptionator is launched by the command-line. Assuming you
have followed the instructions in Installation, open your terminal 
and change to the transcriptionator directory.

`% cd <transcriptionator_path>`

You can get help on using transcriptionator with

`% ./bin/transcriptionator -h` 

You can issue some switches like -r for resetting the project, -v for verbose,
and -q for quiet. These are all documented with the -h call shown above

You create annotate your audio files (i.e., create project directories of 
annotated results) with a command like

`% ./bin/transcriptionator path1 path2 path3` 

transcriptionator requires an audio file in most standard formats. 
For example, wav, mp3, and m4a are all supported. The arguments are 
the paths to any such file. The results are in a folder with the same 
name as your audio file (minus the extension).

A log showing the progress of transcriptionator will keep you
informed on progress. On a modern macbook pro as of 2024, processing 
takes around 1 minute per five minutes of original audio. So for 
large files or for an older machine (or one with fewer cores), the
processing can take a really long time. Be patient and watch the
log messages for feedback.

## Editing Results
When the analysis is finished, transcriptionator will open the results 
in your local web browser. Alternatively, you can always double click
the index.html file in that directory to open the UI in a web browser.

In your local browser, you can freely edit meta information, who is speaking,
and their transcribed words. When you are finished, you can hit a button on
the bottom of the page to save the final transcript.

If you want to save a partial result so that you can return to editing later, 
you can export a special file (cache.js) that you place in the root of the 
output results directory. When you load 

## Security
During annotation and editing, no access to the network is required. 
No data is transmitted off of your computer. Of course, all normal security
considerations are still valid (e.g., a hacker could access files on your 
computer). For added security, you could disconnect your network while 
annotating transcripts, securely zip the results, then reconnect your
network.

## Speek