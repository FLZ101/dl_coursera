[![](https://img.shields.io/pypi/v/dl_coursera)](https://pypi.org/project/dl-coursera/)[![](https://github.com/FLZ101/dl_coursera/actions/workflows/test-single.yml/badge.svg)](https://github.com/FLZ101/dl_coursera/actions/workflows/test-single.yml)[![](https://img.shields.io/github/license/FLZ101/dl_coursera)](https://github.com/FLZ101/dl_coursera/blob/master/LICENSE.txt)[![](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Todo

- [x] Lectures (videos, subtitles, slides)
- [x] Readings
- [ ] Jupyter notebooks
- [ ] Quizs

## Install

Python **⩾3.8** is required.

Install the `dl_coursera` package in a virtual environment.

```
$ pip install -U dl_coursera
$ dl_coursera --version
```

Alternatively, you can download `dl_coursera` as a single executable from [https://github.com/FLZ101/dl_coursera/releases/](https://github.com/FLZ101/dl_coursera/releases/). **Note**:

* This may not work if your OS is outdated
* On Windows, SmartScreen may prevent execution of the executable

## How-to

1. Get the cookies file

   Sign into [Coursera](https://www.coursera.org/), then use a browser extension to export cookies as a cookies file which will expire in about two weeks.

   For Chrome/Edge/Firefox, you can use the **Cookie-Editor** extension.

   ![](https://raw.githubusercontent.com/FLZ101/dl_coursera/master/doc/cookies.png)

2. Enroll

   Navigate to homepage of the **specialization**/**course** you'd like to download, you can see its **slug** at the address bar. **Enroll** in.

   ![](https://raw.githubusercontent.com/FLZ101/dl_coursera/master/doc/enroll.png)

3. Download

   ```
   dl_coursera --cookies path_of_the_cookies_file --outdir output_directory slug
   ```

   For example:

   ```
   $ dl_coursera --cookies cookies.txt --outdir __data advanced-modeling
   ███████████████████████████████ [100%] 56/56 Crawling...
   ███████████████████████████████ [100%] 212/212 Downloading...
   Done :-)
   ```

## Troubleshooting

1. Check your network

2. Make sure you have enrolled in the specialization/course

3. If the cookies file might have expired, try getting a new one

4. Try upgrading to the latest version

5. Remove the directory `<output-directory>/<slug>/.cache` and try again

6. Visit [the issues page](https://github.com/FLZ101/dl_coursera/issues?q=is:issue). You may find a solution if others has encountered similar issues.

   Or you could create a new issue describing what is going wrong and the steps to reproduce it. Don't forget to attach the file `<output-directory>/<slug>/.cache/main.log` if it exists.
