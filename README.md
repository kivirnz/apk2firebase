# apk2firebase
An intuitive way to parse Firebase credentials from .apk files and automatically test them

**You must have [apktool](https://github.com/iBotPeaches/Apktool) added to your system PATH before you run this.**

![apk2firebase logo](https://kivir.pet/assets/images/apk2firebase-logo.png)

Usage:\
Single file: ```python apk2firebase.py filename.apk```\
Multiple files: ```python apk2firebase.py -d apks/```\
Skip Firebase connection tests: ```python apk2firebase.py filename.apk --no-test```\
Tee output to file: ```python apk2firebase.py filename.apk -o output.txt```\

To do list:
- Add the ability to test account creation permissions
