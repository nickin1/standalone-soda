# standalone-soda

Google Chrome includes a Live Caption feature that uses a Speech-On-Device API (SODA) to transcribe audio. The feature can be turned on in settings:

![live captions settings](static/image.png)

When enabled, Chrome fetches SODA as an extension containing the necessary binary and language models.

By default, the SODA binary verifies its execution context, and so cannot be used outside of Chrome. This project provides a framework for using a modified version of the binary on MacOS (M1), so that it can be used to transcribe audio files directly, without live audio input:

[](https://github.com/user-attachments/assets/18692553-ba87-4af8-8c71-7e9bd4da4995)

I cannot provide a modified version of the binary, however `download_soda.py` will fetch `libsoda.so` (the SODA binary) and as well as the english language models. From there, you can use a tool like [Ghidra](https://github.com/NationalSecurityAgency/ghidra) to modify the binary yourself. 

There are many supported languages for SODA, which Chrome can download for you from the Live Captions settings, and you access them at `~/Library/Application Support/Google/Chrome/SODALanguagePacks` and copy them over for use here.

### Usage

1. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```

2. Download SODA

    ```bash
    python3 download_soda.py
    ```

    the binary will be downloaded to `lib/libsoda.so`, and language models will be downloaded to `models/en-US`.

3. Patch the binary using Ghidra, or a similar tool. see notes below for a hint :\)

4. Set the appropriate sample rate and channel count in `config.py`, as well as the path to the patched binary. 

    - These settings are not automatically selected for you, because in some cases I've found that the binary will do some automatic conversion, e.g. 48kHz -> 16kHz. It is reccomended, however, to set the exact values in accordance with the audio file you are transcribing. You can use `ffprobe` (part of `ffmpeg`) or the `-p` flag when running `recognition.py` to view this information.

5. Run

    ```bash
    python3 recognition.py <audio_file.wav> [-l <language>] [-p]
    ```
    
    where `<language>` is the language of the audio file, english if omitted. See `recognition.py` for supported languages, you must have the language models downloaded for the language you are using. `-p` will print the audio file's sample rate and channel count.

### Helpful notes:

- The binary fetched by `download_soda.py` is the one that Google Chrome fetches for use on a MacOS M1 device, other architectures will not work, although you can find a version for your architecture if you know where to look. 

- Patching hint: the binary calls some functions that **verify** execution context by checking the call stack.

- Even if patched correctly, I've found that the binary might not work unless it is re-signed using MacOS's `codesign` tool.

- Unfortuntely, the binary does not give particularly useful debug output, so any errors are difficult to track down. If you still want to see its output, you can reroute the stderr redirect in `recognition.py` to a file, instead of `/dev/null`.

- I've tested it using wav files, with different sample rates, as well as both mono and stereo files. Higher sample rates, e.g. 48kHz, seem to produce better results, even though as far as I can tell the binary will convert inputted audio to 16kHz. It's recommended to leave the settings as is.

Special thanks to this [blog post](https://hackaday.io/project/164399/logs) for the idea.



