## Version - 2019.09.03
* Add [Click]() for command-line usage
* Made Pushover Notifications Optional with `-n/--notifications` flag
* `ChannelIdentification` switch `-c (--channels) 1/2`

## Step 0
1. Define your aws credentials in the ~/.aws/credentials
2. Define your default region in the ~/.aws/config

## Step 1
Run Audio Splitter and Link to the file you want to transcribe.

This will add the file to the transcription bucket and start the transcription process.

## Step 2
Run `build_json.py` and give it the json file containing the transcription data.
